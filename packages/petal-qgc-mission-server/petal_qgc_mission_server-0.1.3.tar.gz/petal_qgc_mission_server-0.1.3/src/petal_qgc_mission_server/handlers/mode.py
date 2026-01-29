"""Mode and state message handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import logger

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..adapter_state import AdapterState

# PX4 custom mode constants
PX4_CUSTOM_MAIN_MODE_AUTO = 4
PX4_CUSTOM_SUB_MODE_AUTO_TAKEOFF = 2
PX4_CUSTOM_SUB_MODE_AUTO_MISSION = 4
PX4_CUSTOM_SUB_MODE_AUTO_RTL = 5
PX4_CUSTOM_SUB_MODE_AUTO_LAND = 6


class ModeHandler:
    """Handle mode-related MAVLink messages."""
    
    def __init__(self, adapter_state: AdapterState):
        """Initialize mode handler.
        
        Args:
            adapter_state: The adapter state to update
        """
        self.vs = adapter_state
    
    def handle_heartbeat(self, msg) -> None:
        """Handle HEARTBEAT message - extract mode and armed state from autopilot.
        
        Args:
            msg: The HEARTBEAT message
        """
        # Only process heartbeats from autopilot (not GCS)
        msg_type = getattr(msg, 'type', None)
        if msg_type == mavutil.mavlink.MAV_TYPE_GCS:
            return  # Ignore GCS heartbeats
        
        base_mode = getattr(msg, 'base_mode', 0)
        custom_mode = getattr(msg, 'custom_mode', 0)
        system_status = getattr(msg, 'system_status', None)
        
        # Update armed state from base_mode
        armed = bool(base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        if self.vs.armed != armed:
            logger.info(f"Armed state changed: {self.vs.armed} -> {armed} (from HEARTBEAT)")
            self.vs.armed = armed
        
        # Update custom_mode
        if custom_mode != self.vs.custom_mode:
            self.vs.custom_mode = custom_mode
            # Decode PX4 custom mode
            main_mode = (custom_mode >> 16) & 0xFF
            sub_mode = (custom_mode >> 24) & 0xFF
            logger.debug(f"Custom mode updated: {custom_mode} (main={main_mode}, sub={sub_mode})")
        
        # Update system status
        if system_status is not None and system_status != self.vs.system_status:
            self.vs.system_status = system_status
    
    def handle_set_mode(self, msg) -> None:
        """Handle SET_MODE message.
        
        Args:
            msg: The SET_MODE message
        """
        tgt = getattr(msg, 'target_system', None)
        base_mode = getattr(msg, 'base_mode', None)
        custom_mode = getattr(msg, 'custom_mode', None)
        
        # Only process if target matches (or no target specified)
        if tgt is None or tgt == 1:  # Assuming system ID 1
            if custom_mode is not None:
                self.vs.custom_mode = custom_mode
                main_mode = (custom_mode >> 16) & 0xFF
                sub_mode = (custom_mode >> 24) & 0xFF
                
                if main_mode == PX4_CUSTOM_MAIN_MODE_AUTO:
                    if sub_mode == PX4_CUSTOM_SUB_MODE_AUTO_MISSION:
                        self.vs.mission_state = 'ACTIVE'
                    elif sub_mode == PX4_CUSTOM_SUB_MODE_AUTO_RTL:
                        self.vs.returning = True
                    elif sub_mode == PX4_CUSTOM_SUB_MODE_AUTO_LAND:
                        self.vs.landing = True
            
            if base_mode is not None:
                armed = bool(base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                self.vs.armed = armed
                self.vs.system_status = (
                    mavutil.mavlink.MAV_STATE_ACTIVE if armed else mavutil.mavlink.MAV_STATE_STANDBY
                )
