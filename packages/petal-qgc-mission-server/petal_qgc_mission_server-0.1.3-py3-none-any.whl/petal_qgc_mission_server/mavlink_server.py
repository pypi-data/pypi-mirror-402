"""Mission protocol handler (no simulation or telemetry)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from . import logger
from .config import CURRENT_MISSION_PATH
from .connection import MavlinkConnection
from .mission_handler import MissionProtocolHandler
from .adapter_state import AdapterState
from .handlers.router import MessageRouter
from .handlers.gps import GPSHandler
from .handlers.mode import ModeHandler
from .handlers.command import CommandHandler
from .handlers.parameter import ParameterHandler
from .handlers.bridge import MissionProgressBridge

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed to run the simulator") from exc

from petal_app_manager.proxies.external import MavLinkExternalProxy
from petal_app_manager.proxies.redis import RedisProxy


class QGCMavlinkServer:
    """Simplified mission protocol handler (no simulation/telemetry)."""

    def __init__(
        self,
        mavlink_proxy: MavLinkExternalProxy,
        redis_proxy: Optional[RedisProxy] = None,
    ):
        """Initialize QGC MAVLink server.
        
        Args:
            mavlink_proxy: The MAVLink external proxy
            redis_proxy: Optional Redis proxy for LeafSDK communication
        """
        # Core components
        self.vs = AdapterState()
        self.redis_proxy = redis_proxy
        
        # Protocol handlers (existing)
        self.mission = MissionProtocolHandler(self.vs, CURRENT_MISSION_PATH, redis_proxy=redis_proxy)
        self.params = ParameterHandler()
        self.commands = CommandHandler(self.vs, self.mission)
        
        # New: Message handlers
        self.gps_handler = GPSHandler(self.vs)
        self.mode_handler = ModeHandler(self.vs)
        
        # New: Message router
        self.router = MessageRouter()
        self._register_message_handlers()
        
        # Create connection with message filter based on registered handlers
        message_filter = self.router.get_handled_message_types()
        self.conn = MavlinkConnection(mavlink_proxy, message_filter=message_filter)
        
        # New: LeafSDK bridge
        self.progress_bridge = MissionProgressBridge(
            redis_proxy,
            self.vs,
            self.mission,
            self.conn,
            self._send_statustext
        )
        self.progress_bridge.setup_listeners()
        
        # Runtime state
        self.running = False
        self.loop_task: Optional[asyncio.Task] = None
    
    def _register_message_handlers(self) -> None:
        """Register all message handlers with the router."""
        # GPS messages
        self.router.register('GLOBAL_POSITION_INT', self.gps_handler.handle_global_position_int)
        self.router.register('GPS_RAW_INT', self.gps_handler.handle_gps_raw_int)
        self.router.register('SET_GPS_GLOBAL_ORIGIN', self.gps_handler.handle_set_gps_global_origin)
        self.router.register('HOME_POSITION', self.gps_handler.handle_home_position)
        self.router.register('GPS_GLOBAL_ORIGIN', self.gps_handler.handle_gps_global_origin)
        self.router.register('LOCAL_POSITION_NED', self.gps_handler.handle_local_position_ned)
        
        # Mode/State
        self.router.register('HEARTBEAT', self.mode_handler.handle_heartbeat)
        self.router.register('SET_MODE', self.mode_handler.handle_set_mode)
        
        # Mission protocol messages
        self.router.register('MISSION_COUNT', lambda msg: self.mission.handle_mission_count(msg, self.conn))
        self.router.register('MISSION_ITEM_INT', lambda msg: self.mission.handle_mission_item_int(msg, self.conn))
        self.router.register('MISSION_ITEM', lambda msg: self.mission.handle_mission_item(msg, self.conn))
        self.router.register('MISSION_REQUEST_LIST', lambda msg: self.mission.handle_mission_request_list(msg, self.conn))
        self.router.register('MISSION_REQUEST_INT', lambda msg: self.mission.handle_mission_request_int(msg, self.conn))
        self.router.register('MISSION_REQUEST', lambda msg: self.mission.handle_mission_request(msg, self.conn))
        self.router.register('MISSION_ACK', lambda msg: self.mission.handle_mission_ack(msg))
        self.router.register('MISSION_CLEAR_ALL', lambda msg: self.mission.handle_mission_clear_all(msg, self.conn))
        self.router.register('MISSION_SET_CURRENT', self._handle_mission_set_current)
        
        # Command messages
        self.router.register('COMMAND_LONG', lambda msg: self.commands.handle_command_long(msg, self.conn))
        self.router.register('COMMAND_INT', self._handle_command_int)
        
        # Parameter messages
        self.router.register('PARAM_REQUEST_LIST', lambda msg: self.params.handle_param_request_list(msg, self.conn))
        self.router.register('PARAM_REQUEST_READ', lambda msg: self.params.handle_param_request_read(msg, self.conn))
        self.router.register('PARAM_SET', lambda msg: self.params.handle_param_set(msg, self.conn))

    def _handle_mission_set_current(self, msg) -> None:
        """Handle MISSION_SET_CURRENT message (Adjust Current Waypoint)."""
        seq = getattr(msg, 'seq', 0)
        old_seq = self.vs.current_mission_item
        self.vs.current_mission_item = seq
        
        # Get waypoint info if available
        waypoint_info = ""
        if self.mission and seq < len(self.mission.waypoints):
            wp = self.mission.waypoints[seq]
            waypoint_info = f" (lat={wp.get('lat', 'N/A')}, lon={wp.get('lon', 'N/A')}, alt={wp.get('alt', 'N/A')}m)"
        
        logger.warning(
            "\n" + "="*80 + "\n"
            "Adjust Current Waypoint Command Received (MISSION_SET_CURRENT)\n"
            f"  Previous waypoint: {old_seq}\n"
            f"  New waypoint: {seq}{waypoint_info}\n"
            "\n"
            "Suggested Mission Alternative:\n"
            "  Option 1: Skip to waypoint (if mission supports it)\n"
            "    - Send Redis command to LeafSDK: mission.skip_to_step\n"
            f'    - Payload: {{"step_id": "Waypoint{seq}"}}\n'
            "\n"
            "  Option 2: Generate new mission from current position to waypoint {seq}\n"
            "    - Calculate path from current GPS to waypoint {seq}\n"
            "    - Create new mission graph with remaining waypoints\n"
            "    - Upload to LeafSDK\n"
            "\n"
            "Note: This command is currently LOGGED ONLY.\n"
            "The mission will NOT automatically skip to this waypoint.\n"
            "="*80
        )
    
    def _handle_command_int(self, msg) -> None:
        """Handle COMMAND_INT message."""
        logger.info("COMMAND_INT received (not fully implemented): %s", msg)

    @property
    def is_running(self) -> bool:
        """Check if the server is running.
        
        Returns:
            True if running, False otherwise
        """
        return self.running

    async def start(self) -> None:
        """Start the mission protocol handler."""
        if self.running:
            logger.info("Mission protocol handler already running")
            return
        logger.info("Starting mission protocol handler")
        self.running = True
        self.loop_task = asyncio.create_task(self._main_loop())

    async def stop(self) -> None:
        """Stop the mission protocol handler."""
        if not self.running:
            return
        logger.info("Stopping mission protocol handler")
        self.running = False
        if self.loop_task:
            try:
                await asyncio.wait_for(self.loop_task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Main loop did not stop gracefully")
                self.loop_task.cancel()

    async def _main_loop(self) -> None:
        """Main message processing loop."""
        try:
            while self.running:
                self._drain_messages()
                await asyncio.sleep(0.05)  # 20 Hz message processing
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
            raise
        except Exception:
            logger.exception("Mission protocol handler loop crashed")
            raise
        finally:
            self.running = False

    def close(self) -> None:
        """Close the connection."""
        self.conn.close()

    def _drain_messages(self) -> None:
        """Drain all pending messages from the queue."""
        while True:
            msg = self.conn.receive_message(blocking=False)
            if not msg:
                break
            self._handle_message(msg)

    def _handle_message(self, msg) -> None:
        """Route MAVLink message to appropriate handler.
        
        Args:
            msg: The MAVLink message
        """
        try:
            msg_type = msg.get_type()
            logger.debug(f"Processing message: {msg_type}")  # Changed from INFO to DEBUG
        except Exception:
            logger.warning(f"Unable to get message type: {type(msg)}")
            return
        
        # Route through the message router
        if not self.router.route(msg):
            logger.debug(f"Unhandled message type: {msg_type}")

    def _send_statustext(self, text: str, severity: int = None) -> None:
        """Send a STATUSTEXT message to GCS.
        
        Args:
            text: The status text to send
            severity: The severity level (default: MAV_SEVERITY_INFO)
        """
        if severity is None:
            severity = mavutil.mavlink.MAV_SEVERITY_INFO
        
        # Truncate text to 50 characters (MAVLink STATUSTEXT limit)
        text = text[:50]
        
        try:
            msg = self.conn.mav.statustext_encode(severity, text.encode('utf-8'))
            self.conn.send_message(msg)
            logger.debug(f"Sent STATUSTEXT: {text}")
        except Exception as exc:
            logger.warning(f"Failed to send STATUSTEXT: {exc}")

    def status(self) -> Dict[str, Any]:
        """Get server status.
        
        Returns:
            Dictionary with server status information
        """
        return {
            'connection': self.conn.connection_label,
            'armed': self.vs.armed,
            'mission_state': self.vs.mission_state,
            'mode': self.vs.mode,
            'system_status': self.vs.system_status,
            'current_mission_item': self.vs.current_mission_item,
            'mission_count': len(self.mission.waypoints),
            'message_stats': self.conn.get_stats(),
        }

    def load_mission(self, path: Path) -> int:
        """Load a mission from a file.
        
        Args:
            path: Path to the mission file
            
        Returns:
            Number of waypoints loaded
        """
        mission_path = Path(path)
        if not mission_path.exists():
            raise FileNotFoundError(mission_path)
        loaded = self.mission.load_qgc_waypoints(str(mission_path))
        self.vs.current_mission_item = 0
        self.vs.mission_state = 'IDLE'
        if loaded:
            logger.info("Loaded mission plan %s", mission_path)
            if mission_path != CURRENT_MISSION_PATH:
                self.mission.save_current_mission()
            self.mission.push_mission_to_gcs(self.conn)
        return self.mission.waypoint_total()
