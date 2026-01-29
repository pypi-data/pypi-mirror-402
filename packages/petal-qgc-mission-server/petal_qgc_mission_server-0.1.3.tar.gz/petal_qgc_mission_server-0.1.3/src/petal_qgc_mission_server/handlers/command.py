"""Command message handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .. import logger

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..adapter_state import AdapterState
    from ..connection import MavlinkConnection
    from ..mission_handler import MissionProtocolHandler


class CommandHandler:
    """Handle MAVLink commands related to missions."""
    
    def __init__(
        self, 
        adapter_state: AdapterState, 
        mission_handler: Optional[MissionProtocolHandler] = None
    ):
        """Initialize command handler.
        
        Args:
            adapter_state: The adapter state to update
            mission_handler: Optional mission protocol handler
        """
        self.vs = adapter_state
        self.mission = mission_handler
        self._handlers = {
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM: self._handle_arm_disarm,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF: self._handle_takeoff,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH: self._handle_rtl,
            mavutil.mavlink.MAV_CMD_NAV_LAND: self._handle_land,
            mavutil.mavlink.MAV_CMD_MISSION_START: self._handle_mission_start,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE: self._handle_set_mode,
            mavutil.mavlink.MAV_CMD_DO_SET_HOME: self._handle_set_home,
            mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED: self._handle_change_speed,
            mavutil.mavlink.MAV_CMD_DO_REPOSITION: self._handle_goto_location,
        }

    def handle_command_long(self, msg, conn: MavlinkConnection):
        """Handle COMMAND_LONG message.
        
        Args:
            msg: The COMMAND_LONG message
            conn: The MAVLink connection
        """
        cmd = msg.command
        logger.info(f"Received COMMAND_LONG: {cmd}")
        
        handler = self._handlers.get(cmd)
        if handler:
            handler(msg, conn)
        else:
            logger.info(f"Unsupported command: {cmd}")
            self.send_command_ack(conn, cmd, mavutil.mavlink.MAV_RESULT_UNSUPPORTED)

    def _handle_arm_disarm(self, msg, conn: MavlinkConnection):
        """Handle ARM/DISARM command."""
        arm = msg.param1 > 0.5
        self.vs.armed = arm
        self.vs.system_status = (
            mavutil.mavlink.MAV_STATE_ACTIVE if arm else mavutil.mavlink.MAV_STATE_STANDBY
        )
        logger.info(f"Vehicle {'armed' if arm else 'disarmed'} (intercepted)")
        # Silent adapter: no ACK

    def _handle_takeoff(self, msg, conn: MavlinkConnection):
        """Handle TAKEOFF command."""
        target_alt = msg.param7
        self.vs.taking_off = True
        self.vs.mission_state = 'TAKEOFF'
        
        # Update home position to current position on takeoff to fix relativity
        self.vs.home_lat = self.vs.lat
        self.vs.home_lon = self.vs.lon
        self.vs.home_alt = self.vs.alt
        
        logger.info(
            f"Takeoff command: target altitude {target_alt}m, "
            f"home set to current position: lat={self.vs.lat/1e7:.7f}, "
            f"lon={self.vs.lon/1e7:.7f}, alt={self.vs.alt/1000.0:.2f}m (intercepted)"
        )
        # Silent adapter: no ACK

    def _handle_rtl(self, msg, conn: MavlinkConnection):
        """Handle RTL command."""
        self.vs.returning = True
        self.vs.mission_state = 'RTL'
        logger.info("Return to launch command (intercepted)")
        # Silent adapter: no ACK

    def _handle_land(self, msg, conn: MavlinkConnection):
        """Handle LAND command."""
        self.vs.landing = True
        self.vs.mission_state = 'LANDING'
        logger.info("Land command (intercepted)")
        # Silent adapter: no ACK

    def _handle_mission_start(self, msg, conn: MavlinkConnection):
        """Handle MISSION_START command."""
        if self.mission and self.mission.waypoints:
            self.vs.mission_state = 'ACTIVE'
            self.vs.current_mission_item = 0
            logger.info("Mission started (intercepted)")
            # Silent adapter: no ACK
        else:
            logger.warning("Mission start requested but no mission loaded")
            # Silent adapter: no ACK (or maybe we should ACK failure? Plan says remove ACKs)

    def _handle_set_mode(self, msg, conn: MavlinkConnection):
        """Handle SET_MODE command."""
        custom_mode = int(msg.param2)
        self.vs.custom_mode = custom_mode
        logger.info(f"Set mode: custom_mode={custom_mode} (intercepted)")
        # Silent adapter: no ACK

    def _handle_set_home(self, msg, conn: MavlinkConnection):
        """Handle SET_HOME command."""
        # Refuse SET_HOME command - not working correctly
        # TODO: Fix home position handling and coordinate with LeafSDK for RTL
        logger.warning("SET_HOME command refused - feature disabled due to incorrect behavior")
        self.send_command_ack(conn, msg.command, mavutil.mavlink.MAV_RESULT_UNSUPPORTED)

    def _handle_change_speed(self, msg, conn: MavlinkConnection):
        """Handle CHANGE_SPEED command."""
        #ToDo: Verify if this is saved as a mission step in the mission plan
        speed_type = int(msg.param1)  # 0=Airspeed, 1=Ground Speed
        speed = float(msg.param2)  # Speed in m/s
        throttle = float(msg.param3)  # Throttle % (-1 = no change)
        
        if speed > 0:
            self.vs.target_speed = speed
            logger.info(f"Speed change command: type={speed_type}, speed={speed} m/s, throttle={throttle}%")
            self.send_command_ack(conn, msg.command, mavutil.mavlink.MAV_RESULT_ACCEPTED)
        else:
            logger.warning(f"Invalid speed change command: speed={speed}")
            self.send_command_ack(conn, msg.command, mavutil.mavlink.MAV_RESULT_FAILED)

    def _handle_goto_location(self, msg, conn: MavlinkConnection):
        """Handle MAV_CMD_DO_REPOSITION (GoTo Location) command."""
        ground_speed = msg.param1  # -1 = use default
        bitmask = int(msg.param2)  # 0=normal, 1=loiter after reaching
        loiter_radius = msg.param3
        yaw = msg.param4
        lat = msg.param5  # degrees
        lon = msg.param6  # degrees
        alt = msg.param7  # meters
        
        logger.warning(
            "\n" + "="*80 + "\n"
            "GoTo Location Command Received (MAV_CMD_DO_REPOSITION)\n"
            f"  Target GPS: lat={lat:.7f}, lon={lon:.7f}, alt={alt:.1f}m\n"
            f"  Speed: {ground_speed:.1f} m/s (or default if -1)\n"
            f"  Loiter: {'Yes' if bitmask & 1 else 'No'}, radius={loiter_radius:.1f}m\n"
            f"  Yaw: {yaw:.1f} degrees\n"
            "\n"
            "Suggested Mission Alternative:\n"
            "  {\n"
            '    "nodes": [\n'
            '      {\n'
            '        "name": "GotoLocation",\n'
            '        "type": "GotoLocalPosition",\n'
            '        "params": {\n'
            f'          "target_gps": [{lat}, {lon}, {alt}],\n'
            f'          "speed": {ground_speed if ground_speed > 0 else 0.5},\n'
            f'          "yaw_deg": {yaw}\n'
            '        }\n'
            '      }\n'
            '    ]\n'
            "  }\n"
            "\n"
            "Note: This command is currently NOT implemented.\n"
            "The drone will NOT navigate to this location.\n"
            "="*80
        )
        
        # Silent adapter: no ACK (command not supported)
        # If you want to reject it explicitly:
        # self.send_command_ack(conn, msg.command, mavutil.mavlink.MAV_RESULT_UNSUPPORTED)
    
    def send_command_ack(self, conn: MavlinkConnection, command: int, result: int):
        """Send command acknowledgment.
        
        Args:
            conn: The MAVLink connection
            command: The command ID
            result: The result code
        """
        msg = conn.mav.command_ack_encode(command, result)
        conn.send_message(msg)
