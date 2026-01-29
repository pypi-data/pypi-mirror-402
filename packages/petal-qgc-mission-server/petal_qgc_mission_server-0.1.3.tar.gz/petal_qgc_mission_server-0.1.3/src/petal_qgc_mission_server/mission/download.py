"""Mission download handler for sending missions to GCS."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional

from .. import logger
from .models import DownloadState
from .storage import MissionStorage
from .utils import extract_src_ids

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection


class MissionDownloadHandler:
    """Handles mission download protocol to GCS.
    
    Responsibilities:
    - Handle MISSION_REQUEST_LIST, MISSION_REQUEST_INT, MISSION_REQUEST messages
    - Manage download state
    - Send waypoints to GCS
    - Send mission count
    - Request mission load from petal-leafsdk via Redis
    """
    
    SUPPORTED_MISSION_TYPES = {
        getattr(mavutil.mavlink, "MAV_MISSION_TYPE_MISSION", 0)
    }
    
    def __init__(self, storage: MissionStorage, redis_proxy=None):
        """Initialize download handler.
        
        Args:
            storage: Mission storage instance
            redis_proxy: Redis proxy for communication (optional)
        """
        self.storage = storage
        self.redis_proxy = redis_proxy
        self.state = DownloadState()

    
    def handle_mission_request_list(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST_LIST message.
        
        Args:
            msg: MISSION_REQUEST_LIST message
            conn: MAVLink connection
        """
        src_system, src_component = extract_src_ids(msg)
        self.state.target_system = src_system if src_system is not None else msg.target_system
        self.state.target_component = src_component if src_component is not None else msg.target_component
        
        requested_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        
        # Check if supported
        if requested_type is not None and requested_type not in self.SUPPORTED_MISSION_TYPES:
            logger.info(f"MISSION_REQUEST_LIST for unsupported mission type {requested_type}")
            self._send_empty_mission_response(conn, requested_type)
            return
        
        # Request mission load from petal-leafsdk via Redis
        self._request_mission_load()
        
        total = self.storage.total()
        logger.info(f"MISSION_REQUEST_LIST from {self.state.target_system}:{self.state.target_component} -> {total} waypoints")
        
        self.state.in_progress = total > 0
        self.state.pending_plan = total > 0
        
        self.send_mission_count(conn, self.state.target_system, self.state.target_component, requested_type, total)
        
        if total == 0:
            self.state.reset()
    
    def _request_mission_load(self) -> None:
        """Request mission load from petal-leafsdk via Redis."""
        if self.redis_proxy is None:
            logger.debug("Redis proxy not available; skipping mission load request")
            return
        
        import json
        import uuid
        
        message_id = f"mission-load-{uuid.uuid4()}"
        redis_message = {
            "message_id": message_id,
            "command": "mission.load",
            "payload": {},
            "source": "petal-qgc-mission-server",
        }
        
        try:
            from .translation import QGC_MISSION_CMD_CHANNEL
            subscribers = self.redis_proxy.publish(
                channel=QGC_MISSION_CMD_CHANNEL,
                message=json.dumps(redis_message),
            )
            logger.info(
                f"Requested mission load via Redis (message_id={message_id}, subscribers={subscribers})"
            )
        except Exception as exc:
            logger.warning(f"Failed to request mission load via Redis: {exc}")

    
    def handle_mission_request_int(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST_INT message.
        
        Args:
            msg: MISSION_REQUEST_INT message
            conn: MAVLink connection
        """
        seq = getattr(msg, 'seq', None)
        if seq is None:
            seq = getattr(msg, 'mission_index', 0)
        
        src_system, src_component = extract_src_ids(msg)
        target_system = src_system if src_system is not None else self.state.target_system
        target_component = src_component if src_component is not None else self.state.target_component
        
        requested_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        
        if requested_type is not None and requested_type not in self.SUPPORTED_MISSION_TYPES:
            logger.info(f"MISSION_REQUEST_INT for unsupported mission type {requested_type}")
            self._send_empty_mission_response(conn, requested_type)
            return
        
        logger.info(f"MISSION_REQUEST_INT for seq {seq} (target {target_system}:{target_component})")
        
        sent = self.send_stored_waypoint(conn, seq, target_system, target_component)
        
        if sent and seq + 1 >= self.storage.total():
            self.state.in_progress = False
    
    def handle_mission_request(self, msg, conn: MavlinkConnection) -> None:
        """Handle MISSION_REQUEST message (non-INT variant).
        
        Args:
            msg: MISSION_REQUEST message
            conn: MAVLink connection
        """
        seq = getattr(msg, 'seq', 0)
        src_system, src_component = extract_src_ids(msg)
        target_system = src_system if src_system is not None else self.state.target_system
        target_component = src_component if src_component is not None else self.state.target_component
        
        requested_type = getattr(msg, 'mission_type', None) if hasattr(msg, 'mission_type') else None
        
        if requested_type is not None and requested_type not in self.SUPPORTED_MISSION_TYPES:
            logger.info(f"MISSION_REQUEST for unsupported mission type {requested_type}")
            self._send_empty_mission_response(conn, requested_type)
            return
        
        logger.info(f"MISSION_REQUEST for seq {seq} (target {target_system}:{target_component})")
        
        sent = self.send_stored_waypoint(conn, seq, target_system, target_component)
        
        if sent and seq + 1 >= self.storage.total():
            self.state.in_progress = False
    
    def send_mission_count(
        self,
        conn: MavlinkConnection,
        target_system: int,
        target_component: int,
        mission_type: Optional[int] = None,
        count: Optional[int] = None
    ) -> None:
        """Send mission count to GCS.
        
        Args:
            conn: MAVLink connection
            target_system: Target system ID
            target_component: Target component ID
            mission_type: Mission type (optional)
            count: Waypoint count (optional, uses storage total if None)
        """
        from .mavlink_helpers import MavlinkMessageBuilder
        
        if count is None:
            count = self.storage.total()
        
        if mission_type is None:
            mission_type = self.storage.get_mission_type()
        
        logger.debug(f"Sending MISSION_COUNT: {count} waypoints to {target_system}:{target_component}")
        
        MavlinkMessageBuilder.mission_count(conn, target_system, target_component, count, mission_type)

    
    def send_stored_waypoint(
        self,
        conn: MavlinkConnection,
        seq: int,
        target_system: Optional[int],
        target_component: Optional[int]
    ) -> bool:
        """Send a stored waypoint to GCS.
        
        Args:
            conn: MAVLink connection
            seq: Waypoint sequence number
            target_system: Target system ID
            target_component: Target component ID
            
        Returns:
            True if sent successfully, False otherwise
        """
        from .mavlink_helpers import MavlinkMessageBuilder
        import math
        
        wp = self.storage.get_waypoint(seq)
        if wp is None:
            logger.warning(f"Requested waypoint {seq} not found")
            return False
        
        # Convert to lat/lon degrees
        lat = wp.lat if wp.lat is not None else (wp.x / 1e7 if wp.x is not None else 0.0)
        lon = wp.lon if wp.lon is not None else (wp.y / 1e7 if wp.y is not None else 0.0)
        
        # Format parameters (handle NaN)
        def fmt(value: float) -> float:
            return 0.0 if math.isnan(value) else value
        
        logger.debug(f"Sending waypoint {seq}: lat={lat:.6f}, lon={lon:.6f}, alt={wp.z:.1f}")
        
        # Use helper to send MISSION_ITEM_INT
        return MavlinkMessageBuilder.mission_item_int(
            conn,
            target_system or 0,
            target_component or 0,
            seq,
            wp.frame,
            wp.command,
            wp.current,
            wp.autocontinue,
            fmt(wp.param1),
            fmt(wp.param2),
            fmt(wp.param3),
            fmt(wp.param4),
            int(lat * 1e7),
            int(lon * 1e7),
            wp.z,
            self.storage.get_mission_type()
        )

    
    def _send_empty_mission_response(
        self,
        conn: MavlinkConnection,
        mission_type: Optional[int]
    ) -> None:
        """Send empty mission response for unsupported types.
        
        Args:
            conn: MAVLink connection
            mission_type: Mission type
        """
        ts = self.state.target_system or 0
        tc = self.state.target_component or 0
        mission_type_val = mission_type if mission_type is not None else 0
        
        self.send_mission_count(conn, ts, tc, mission_type_val, 0)
        self.state.reset()
