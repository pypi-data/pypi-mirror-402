"""Parameter message handler."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .. import logger

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection


class ParameterHandler:
    """Handle parameter requests (minimal implementation for mission protocol)."""
    
    def __init__(self):
        """Initialize parameter handler."""
        # Parameters disabled in silent adapter mode
        self.parameters = {}
        self.param_list = []
        logger.info("Parameter handler initialized (disabled)")

    def handle_param_request_list(self, msg, conn: MavlinkConnection):
        """Handle PARAM_REQUEST_LIST message.
        
        Args:
            msg: The PARAM_REQUEST_LIST message
            conn: The MAVLink connection
        """
        logger.info("Parameter request list received (ignored)")
        # Silent adapter: do not respond
        pass

    def handle_param_request_read(self, msg, conn: MavlinkConnection):
        """Handle PARAM_REQUEST_READ message.
        
        Args:
            msg: The PARAM_REQUEST_READ message
            conn: The MAVLink connection
        """
        logger.info("Parameter request read received (ignored)")
        # Silent adapter: do not respond
        pass

    def handle_param_set(self, msg, conn: MavlinkConnection):
        """Handle PARAM_SET message.
        
        Args:
            msg: The PARAM_SET message
            conn: The MAVLink connection
        """
        pid = msg.param_id.decode("utf-8").rstrip("\x00")
        logger.info(f"Parameter set received for {pid} (ignored)")
        # Silent adapter: do not respond or update
        pass

    def send_param_value(self, conn: MavlinkConnection, pid: str, pval: float, idx: int):
        """Send parameter value.
        
        Args:
            conn: The MAVLink connection
            pid: Parameter ID
            pval: Parameter value
            idx: Parameter index
        """
        ptype = (
            mavutil.mavlink.MAV_PARAM_TYPE_REAL32
            if isinstance(pval, float)
            else mavutil.mavlink.MAV_PARAM_TYPE_INT32
        )
        msg = conn.mav.param_value_encode(
            pid.encode("utf-8"), float(pval), ptype, len(self.parameters), idx
        )
        conn.send_message(msg)
