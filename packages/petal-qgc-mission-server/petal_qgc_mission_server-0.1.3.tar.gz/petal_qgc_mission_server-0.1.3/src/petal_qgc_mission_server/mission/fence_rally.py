"""Fence and rally mission handler."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .. import logger
from .models import EmptyMissionState
from .utils import extract_src_ids

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection


class FenceRallyHandler:
    """Handles fence and rally mission types.
    
    These missions are received but discarded (not stored).
    The adapter responds with empty mission counts.
    """
    
    EMPTY_RESPONSE_MISSION_TYPES = {
        getattr(mavutil.mavlink, "MAV_MISSION_TYPE_FENCE", 1),
        getattr(mavutil.mavlink, "MAV_MISSION_TYPE_RALLY", 2)
    }
    
    def __init__(self):
        """Initialize fence/rally handler."""
        self.state = EmptyMissionState()
    
    def is_fence_or_rally_type(self, mission_type: Optional[int]) -> bool:
        """Check if mission type is fence or rally.
        
        Args:
            mission_type: Mission type to check
            
        Returns:
            True if fence or rally type
        """
        if mission_type is None:
            return False
        return mission_type in self.EMPTY_RESPONSE_MISSION_TYPES
    
    def handle_mission_count(self, msg, conn: MavlinkConnection) -> bool:
        """Handle MISSION_COUNT for fence/rally.
        
        Args:
            msg: MISSION_COUNT message
            conn: MAVLink connection
            
        Returns:
            True if handled (fence/rally type), False otherwise
        """
        count = getattr(msg, 'count', 0)
        mission_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        
        if not self.is_fence_or_rally_type(mission_type):
            return False
        
        src_system, src_component = extract_src_ids(msg)
        
        logger.info(f"Fence/Rally mission upload started: type={mission_type}, count={count}")
        
        self.state.start_upload(mission_type, count, src_system, src_component)
        
        # Request first item
        if count > 0:
            self._request_item(0, conn)
        else:
            self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED)
        
        return True
    
    def handle_mission_item(self, msg, seq: int, conn: MavlinkConnection) -> bool:
        """Handle MISSION_ITEM_INT or MISSION_ITEM for fence/rally.
        
        Args:
            msg: MISSION_ITEM message
            seq: Sequence number
            conn: MAVLink connection
            
        Returns:
            True if handled (fence/rally upload active), False otherwise
        """
        if not self.state.active:
            return False
        
        # Check sequence
        if seq != self.state.expected_seq:
            if seq < self.state.expected_seq:
                logger.info(f"Ignoring already received fence/rally item seq {seq}")
                return True
            
            # Request expected seq
            self._request_item(self.state.expected_seq, conn)
            return True
        
        logger.debug(f"Received fence/rally item {seq} (discarding)")
        
        self.state.expected_seq += 1
        
        # Request next or finalize
        if self.state.expected_seq < self.state.expected_count:
            self._request_item(self.state.expected_seq, conn)
        else:
            logger.info(f"All {self.state.expected_count} fence/rally items received (discarded)")
            self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED)
        
        return True
    
    def handle_mission_request_list(self, msg, conn: MavlinkConnection) -> bool:
        """Handle MISSION_REQUEST_LIST for fence/rally.
        
        Args:
            msg: MISSION_REQUEST_LIST message
            conn: MAVLink connection
            
        Returns:
            True if handled (fence/rally type), False otherwise
        """
        requested_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        
        if not self.is_fence_or_rally_type(requested_type):
            return False
        
        src_system, src_component = extract_src_ids(msg)
        
        logger.info(f"MISSION_REQUEST_LIST for fence/rally type {requested_type}; responding with empty mission")
        
        self._send_empty_response(conn, requested_type, src_system, src_component)
        
        return True
    
    def _request_item(self, seq: int, conn: MavlinkConnection) -> None:
        """Request fence/rally item.
        
        Args:
            seq: Sequence number
            conn: MAVLink connection
        """
        logger.debug(f"Requesting fence/rally item {seq}")
        
        try:
            msg = conn.mav.mission_request_int_encode(
                self.state.partner_system or 0,
                self.state.partner_component or 0,
                seq,
                self.state.mission_type
            )
            conn.send_message(msg)
        except TypeError:
            # Fallback
            try:
                msg = conn.mav.mission_request_int_encode(
                    self.state.partner_system or 0,
                    self.state.partner_component or 0,
                    seq
                )
                if hasattr(msg, "mission_type"):
                    msg.mission_type = self.state.mission_type
                conn.send_message(msg)
            except Exception as exc:
                logger.error(f"Failed to send fence/rally request: {exc}")
    
    def _finalize_upload(self, conn: MavlinkConnection, result: int) -> None:
        """Finalize fence/rally upload.
        
        Args:
            conn: MAVLink connection
            result: Result code
        """
        self._send_ack(conn, result, self.state.mission_type, self.state.partner_system, self.state.partner_component)
        self.state.reset()
    
    def _send_empty_response(
        self,
        conn: MavlinkConnection,
        mission_type: int,
        target_system: Optional[int],
        target_component: Optional[int]
    ) -> None:
        """Send empty mission response.
        
        Args:
            conn: MAVLink connection
            mission_type: Mission type
            target_system: Target system ID
            target_component: Target component ID
        """
        ts = target_system if target_system is not None else 0
        tc = target_component if target_component is not None else 0
        
        # Send count = 0
        try:
            msg = conn.mav.mission_count_encode(ts, tc, 0, mission_type)
            conn.send_message(msg)
        except TypeError:
            msg = conn.mav.mission_count_encode(ts, tc, 0)
            if hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            conn.send_message(msg)
        
        # Send ACK
        self._send_ack(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED, mission_type, ts, tc)
    
    def _send_ack(
        self,
        conn: MavlinkConnection,
        result: int,
        mission_type: int,
        target_system: Optional[int],
        target_component: Optional[int]
    ) -> None:
        """Send mission ACK.
        
        Args:
            conn: MAVLink connection
            result: Result code
            mission_type: Mission type
            target_system: Target system ID
            target_component: Optional[int]
        """
        ts = target_system if target_system is not None else 0
        tc = target_component if target_component is not None else 0
        
        try:
            msg = conn.mav.mission_ack_encode(ts, tc, result, mission_type)
            conn.send_message(msg)
        except TypeError:
            msg = conn.mav.mission_ack_encode(ts, tc, result)
            if hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            conn.send_message(msg)
