"""Mission upload handler for receiving missions from GCS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .. import logger
from ..mission_translator import PetalMissionTranslator
from .models import UploadState, Waypoint
from .storage import MissionStorage
from .utils import extract_src_ids

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection
    from ..adapter_state import AdapterState


class MissionUploadHandler:
    """Handles mission upload protocol from GCS.
    
    Responsibilities:
    - Handle MISSION_COUNT, MISSION_ITEM_INT, MISSION_ITEM messages
    - Manage upload state
    - Validate and store waypoints
    - Request missing waypoints
    """
    
    SUPPORTED_MISSION_TYPES = {
        getattr(mavutil.mavlink, "MAV_MISSION_TYPE_MISSION", 0)
    }
    
    def __init__(self, storage: MissionStorage, adapter_state: AdapterState):
        """Initialize upload handler.
        
        Args:
            storage: Mission storage instance
            adapter_state: Adapter state
        """
        self.storage = storage
        self.vs = adapter_state
        self.state = UploadState()
    
    def handle_mission_count(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_COUNT message.
        
        Args:
            msg: MISSION_COUNT message
            conn: MAVLink connection
        """
        count = getattr(msg, 'count', 0)
        mission_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        src_system, src_component = extract_src_ids(msg)
        
        # Check if supported mission type
        if mission_type is not None and mission_type not in self.SUPPORTED_MISSION_TYPES:
            logger.info(f"Unsupported mission type {mission_type} in MISSION_COUNT")
            return
        
        # Start upload
        if mission_type is None:
            mission_type = getattr(mavutil.mavlink, "MAV_MISSION_TYPE_MISSION", 0)
        
        self.state.start_upload(count, mission_type, src_system, src_component)
        self.storage.clear()
        self.storage.set_mission_type(mission_type)
        
        logger.info(f"Mission upload started: {count} waypoints, type={mission_type}")
        
        # Request first waypoint
        if count > 0:
            self.request_waypoint(0, conn)
        else:
            logger.info("Empty mission received")
            self.state.reset()
    
    def handle_mission_item_int(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_ITEM_INT message.
        
        Args:
            msg: MISSION_ITEM_INT message
            conn: MAVLink connection
        """
        seq = getattr(msg, "seq", 0)
        
        if not self.state.active:
            logger.info("Ignoring MISSION_ITEM_INT while no mission upload in progress")
            return
        
        # Check sequence number
        if seq != self.state.expected_seq:
            if seq == self.state.expected_seq - 1:
                self.state.duplicate_last_seq += 1
                if self.state.duplicate_last_seq >= 2:
                    logger.info("Received duplicate of last waypoint twice; assuming upload complete")
                    self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED, adjust_count=True)
                else:
                    logger.info(f"Received duplicate of last waypoint (seq {seq}) while waiting for {self.state.expected_seq}")
                return
            
            if seq < self.state.expected_seq:
                logger.info(f"Ignoring already received waypoint seq {seq} while awaiting {self.state.expected_seq}")
                return
            
            # Request the expected seq
            self.request_waypoint(self.state.expected_seq, conn)
            return
        
        # Normalize and store waypoint
        lat = msg.x / 1e7
        lon = msg.y / 1e7
        logger.info(f"WP{seq}: lat={lat:.6f}, lon={lon:.6f}, alt={msg.z:.1f}")
        
        wp_dict = PetalMissionTranslator.normalise_waypoint(
            msg.seq, msg.frame, msg.command, msg.current, msg.autocontinue,
            msg.param1, msg.param2, msg.param3, msg.param4,
            int(msg.x), int(msg.y), msg.z,
            self.vs.home_lat, self.vs.home_lon
        )
        
        wp = Waypoint.from_dict(wp_dict)
        self.storage.add_waypoint(wp)
        
        # Clear request attempts for this waypoint
        self.state.request_attempts.pop(seq, None)
        self.state.duplicate_last_seq = 0
        self.state.expected_seq += 1
        
        # Request next or finalize
        if self.state.expected_seq < self.state.waypoint_count:
            self.request_waypoint(self.state.expected_seq, conn)
        else:
            logger.info(f"All {self.state.waypoint_count} WPs received")
            self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED)
    
    def handle_mission_item(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_ITEM message (non-INT variant).
        
        Args:
            msg: MISSION_ITEM message
            conn: MAVLink connection
        """
        seq = getattr(msg, "seq", 0)
        
        if not self.state.active:
            logger.info("Ignoring MISSION_ITEM while no mission upload in progress")
            return
        
        # Check sequence number (same logic as MISSION_ITEM_INT)
        if seq != self.state.expected_seq:
            if seq == self.state.expected_seq - 1:
                self.state.duplicate_last_seq += 1
                if self.state.duplicate_last_seq >= 2:
                    logger.info("Received duplicate of last waypoint twice; assuming upload complete")
                    self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED, adjust_count=True)
                else:
                    logger.info(f"Received duplicate of last waypoint (seq {seq}) while waiting for {self.state.expected_seq}")
                return
            
            if seq < self.state.expected_seq:
                logger.info(f"Ignoring already received waypoint seq {seq} while awaiting {self.state.expected_seq}")
                return
            
            self.request_waypoint(self.state.expected_seq, conn)
            return
        
        # Normalize and store waypoint
        logger.info(f"WP{seq}: lat={msg.x:.6f}, lon={msg.y:.6f}, alt={msg.z:.1f}")
        
        x = int(msg.x * 1e7)
        y = int(msg.y * 1e7)
        wp_dict = PetalMissionTranslator.normalise_waypoint(
            msg.seq, msg.frame, msg.command, msg.current, msg.autocontinue,
            msg.param1, msg.param2, msg.param3, msg.param4,
            x, y, msg.z,
            self.vs.home_lat, self.vs.home_lon
        )
        
        wp = Waypoint.from_dict(wp_dict)
        self.storage.add_waypoint(wp)
        
        # Clear request attempts for this waypoint
        self.state.request_attempts.pop(seq, None)
        self.state.duplicate_last_seq = 0
        self.state.expected_seq += 1
        
        # Request next or finalize
        if self.state.expected_seq < self.state.waypoint_count:
            self.request_waypoint(self.state.expected_seq, conn)
        else:
            logger.info(f"All {self.state.waypoint_count} WPs received")
            self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED)
    
    def request_waypoint(self, seq: int, conn: MavlinkConnection) -> None:
        """Request a waypoint from GCS.
        
        Args:
            seq: Sequence number to request
            conn: MAVLink connection
        """
        from .mavlink_helpers import MavlinkMessageBuilder
        
        # Track request attempts
        attempts = self.state.request_attempts.get(seq, 0) + 1
        self.state.request_attempts[seq] = attempts
        
        if attempts > 5:
            logger.warning(f"Too many request attempts for waypoint {seq}, aborting upload")
            self._finalize_upload(conn, mavutil.mavlink.MAV_MISSION_ERROR)
            return
        
        logger.debug(f"Requesting waypoint {seq} (attempt {attempts})")
        
        # Use helper to send MISSION_REQUEST_INT
        MavlinkMessageBuilder.mission_request_int(
            conn,
            self.state.partner_system or 0,
            self.state.partner_component or 0,
            seq,
            self.state.mission_type
        )

    
    def _finalize_upload(
        self,
        conn: MavlinkConnection,
        result: int,
        adjust_count: bool = False
    ) -> None:
        """Finalize mission upload.
        
        Args:
            conn: MAVLink connection
            result: Result code (MAV_MISSION_ACCEPTED or MAV_MISSION_ERROR)
            adjust_count: If True, adjust waypoint count to expected_seq
        """
        if adjust_count:
            self.state.waypoint_count = min(self.state.waypoint_count, self.state.expected_seq)
        
        logger.info(f"Mission upload finalized with result {result}")
        
        # Call the upload complete callback if set (triggers translation)
        callback = getattr(self, '_upload_complete_callback', None)
        if callback and result == mavutil.mavlink.MAV_MISSION_ACCEPTED:
            try:
                callback(conn)
            except Exception as exc:
                logger.error(f"Error in upload complete callback: {exc}", exc_info=True)
        
        self.state.reset()
    
    def get_upload_complete_callback(self):
        """Get callback to be called when upload is complete.
        
        Returns:
            Callback function or None
        """
        # This will be set by MissionProtocolHandler to trigger translation
        return getattr(self, '_upload_complete_callback', None)
    
    def set_upload_complete_callback(self, callback):
        """Set callback to be called when upload is complete.
        
        Args:
            callback: Callback function
        """
        self._upload_complete_callback = callback
