"""Refactored mission protocol handler - composition root."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from . import logger
from .mission.storage import MissionStorage
from .mission.upload import MissionUploadHandler
from .mission.download import MissionDownloadHandler
from .mission.fence_rally import FenceRallyHandler
from .mission.translation import MissionTranslationService

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from .connection import MavlinkConnection
    from .adapter_state import AdapterState
    from petal_app_manager.proxies.redis import RedisProxy


class MissionProtocolHandler:
    """Refactored mission protocol handler using composition.
    
    This class is now a thin composition root that delegates to specialized handlers:
    - MissionStorage: Waypoint storage and persistence
    - MissionUploadHandler: Receiving missions from GCS
    - MissionDownloadHandler: Sending missions to GCS
    - FenceRallyHandler: Fence/rally mission types
    - MissionTranslationService: MAVLink to LeafSDK conversion
    
    Reduced from 1547 lines to ~200 lines.
    """
    
    def __init__(
        self,
        vs: AdapterState,
        current_mission_path: Path,
        redis_proxy: Optional[RedisProxy] = None,
    ):
        """Initialize mission protocol handler.
        
        Args:
            vs: Adapter state
            current_mission_path: Path to current mission file
            redis_proxy: Redis proxy for LeafSDK communication
        """
        self.vs = vs
        self.current_mission_path = Path(current_mission_path)
        self.redis_proxy = redis_proxy
        
        # Create specialized handlers
        self.storage = MissionStorage()
        self.upload = MissionUploadHandler(self.storage, vs)
        self.download = MissionDownloadHandler(self.storage, redis_proxy)
        self.fence_rally = FenceRallyHandler()
        self.translation = MissionTranslationService(
            self.storage,
            redis_proxy,
            vs,
            debug_dir=current_mission_path.parent
        )
        
        # Set upload complete callback to trigger translation
        self.upload.set_upload_complete_callback(self._on_upload_complete)
        
        # Load existing mission if available
        if self.current_mission_path.exists():
            try:
                self.storage.load_from_file(self.current_mission_path)
                logger.info(f"Loaded existing mission: {self.storage.total()} waypoints")
            except Exception as exc:
                logger.warning(f"Failed to load existing mission: {exc}")
    
    # =========================================================================
    # Upload Protocol (from GCS)
    # =========================================================================
    
    def handle_mission_count(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_COUNT message.
        
        Args:
            msg: MISSION_COUNT message
            conn: MAVLink connection
        """
        # Check if fence/rally type
        if self.fence_rally.handle_mission_count(msg, conn):
            return
        
        # Otherwise, delegate to upload handler
        self.upload.handle_mission_count(msg, conn)
    
    def handle_mission_item_int(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_ITEM_INT message.
        
        Args:
            msg: MISSION_ITEM_INT message
            conn: MAVLink connection
        """
        seq = getattr(msg, "seq", 0)
        
        # Check if fence/rally upload
        if self.fence_rally.handle_mission_item(msg, seq, conn):
            return
        
        # Otherwise, delegate to upload handler
        self.upload.handle_mission_item_int(msg, conn)
    
    def handle_mission_item(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_ITEM message.
        
        Args:
            msg: MISSION_ITEM message
            conn: MAVLink connection
        """
        seq = getattr(msg, "seq", 0)
        
        # Check if fence/rally upload
        if self.fence_rally.handle_mission_item(msg, seq, conn):
            return
        
        # Otherwise, delegate to upload handler
        self.upload.handle_mission_item(msg, conn)
    
    def _on_upload_complete(self, conn: MavlinkConnection) -> None:
        """Callback when mission upload is complete.
        
        Args:
            conn: MAVLink connection
        """
        # Save mission to file
        self.save_current_mission()
        
        # Translate and publish to LeafSDK
        logger.info("Mission upload complete, translating to LeafSDK format...")
        # Pass partner system/component IDs for proper ACK addressing
        partner_system = self.upload.state.partner_system
        partner_component = self.upload.state.partner_component
        self.translation.translate_and_publish(conn, partner_system, partner_component)
    
    # =========================================================================
    # Download Protocol (to GCS)
    # =========================================================================
    
    def handle_mission_request_list(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST_LIST message.
        
        Args:
            msg: MISSION_REQUEST_LIST message
            conn: MAVLink connection
        """
        # Check if fence/rally type
        if self.fence_rally.handle_mission_request_list(msg, conn):
            return
        
        # Otherwise, delegate to download handler
        self.download.handle_mission_request_list(msg, conn)
    
    def handle_mission_request_int(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST_INT message.
        
        Args:
            msg: MISSION_REQUEST_INT message
            conn: MAVLink connection
        """
        self.download.handle_mission_request_int(msg, conn)
    
    def handle_mission_request(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST message.
        
        Args:
            msg: MISSION_REQUEST message
            conn: MAVLink connection
        """
        self.download.handle_mission_request(msg, conn)
    
    def handle_mission_ack(self, msg) -> None:
        """Handle MISSION_ACK message.
        
        Args:
            msg: MISSION_ACK message
        """
        ack_type = getattr(msg, 'type', None)
        if ack_type is not None and ack_type != mavutil.mavlink.MAV_MISSION_ACCEPTED:
            logger.warning(f"MISSION_ACK received with status {ack_type}")
            self.download.state.pending_plan = False
        else:
            logger.info("MISSION_ACK received from GCS")
            if self.download.state.pending_plan:
                logger.info("Mission download complete")
            self.download.state.pending_plan = False
        
        self.download.state.in_progress = False
    
    def handle_mission_clear_all(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_CLEAR_ALL message.
        
        Args:
            msg: MISSION_CLEAR_ALL message
            conn: MAVLink connection
        """
        clear_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        logger.info("MISSION_CLEAR_ALL received (type=%s)", clear_type)
        
        # Clear mission
        self.storage.clear()
        self.vs.current_mission_item = 0
        self.vs.mission_state = "IDLE"
        self.vs.taking_off = False
        self.vs.landing = False
        self.vs.returning = False
        
        self.clear_current_mission_file()
        
        # Send ACK
        self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED, clear_type)
    
    # =========================================================================
    # Persistence
    # =========================================================================
    
    def save_current_mission(self) -> None:
        """Save current mission to file."""
        try:
            self.storage.save_to_file(self.current_mission_path)
        except Exception as exc:
            logger.error(f"Failed to save mission: {exc}")
    
    def clear_current_mission_file(self) -> None:
        """Clear the current mission file."""
        try:
            if self.current_mission_path.exists():
                self.current_mission_path.unlink()
                logger.info(f"Cleared mission file: {self.current_mission_path}")
        except Exception as exc:
            logger.warning(f"Failed to clear mission file: {exc}")
    
    def load_qgc_waypoints(self, path: str) -> bool:
        """Load waypoints from QGC WPL file.
        
        Args:
            path: Path to WPL file
            
        Returns:
            True if loaded successfully
        """
        try:
            count = self.storage.load_from_file(Path(path))
            return count > 0
        except Exception as exc:
            logger.error(f"Failed to load waypoints from {path}: {exc}")
            return False
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def waypoint_total(self) -> int:
        """Get total number of waypoints.
        
        Returns:
            Number of waypoints
        """
        return self.storage.total()
    
    def push_mission_to_gcs(self, conn: MavlinkConnection) -> None:
        """Push mission to GCS (broadcast).
        
        Args:
            conn: MAVLink connection
        """
        total = self.storage.total()
        logger.info(f"Broadcasting mission to GCS: {total} waypoints")
        
        # Use default system/component IDs for broadcast
        self.download.send_mission_count(conn, 255, 0, None, total)
        self.download.state.in_progress = total > 0
        self.download.state.pending_plan = total > 0
    
    def send_mission_current(self, conn: MavlinkConnection) -> None:
        """Send MISSION_CURRENT message.
        
        Args:
            conn: MAVLink connection
        """
        msg = conn.mav.mission_current_encode(self.vs.current_mission_item)
        conn.send_message(msg)
    
    def send_mission_item_reached(self, conn: MavlinkConnection, seq: int) -> None:
        """Send MISSION_ITEM_REACHED message.
        
        Args:
            conn: MAVLink connection
            seq: Sequence number of reached waypoint
        """
        msg = conn.mav.mission_item_reached_encode(seq)
        conn.send_message(msg)
    
    def _send_mission_ack(
        self,
        conn: MavlinkConnection,
        result: int,
        mission_type: Optional[int] = None
    ) -> None:
        """Send mission ACK.
        
        Args:
            conn: MAVLink connection
            result: Result code
            mission_type: Mission type (optional)
        """
        if mission_type is None:
            mission_type = self.storage.get_mission_type()
        
        try:
            msg = conn.mav.mission_ack_encode(0, 0, result, mission_type)
            conn.send_message(msg)
        except TypeError:
            msg = conn.mav.mission_ack_encode(0, 0, result)
            if hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            conn.send_message(msg)
    
    # =========================================================================
    # Backwards Compatibility Properties
    # =========================================================================
    
    @property
    def waypoints(self):
        """Get waypoints as list of dicts (backwards compatibility).
        
        Returns:
            List of waypoint dictionaries
        """
        return self.storage.get_waypoints_as_dicts()
    
    @property
    def step_to_waypoint_map(self):
        """Get step-to-waypoint mapping (backwards compatibility).
        
        Returns:
            Dict mapping step IDs to waypoint sequence numbers
        """
        return self.translation.step_to_waypoint_map
    
    @property
    def waypoint_to_step_map(self):
        """Get waypoint-to-step mapping (backwards compatibility).
        
        Returns:
            Dict mapping waypoint sequence numbers to step IDs
        """
        return self.translation.waypoint_to_step_map
