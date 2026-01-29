"""Mission translation service for converting MAVLink to LeafSDK format."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from .. import logger
from ..mission_translator import MissionTranslator, PositionData
from .storage import MissionStorage

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection
    from ..adapter_state import AdapterState
    from petal_app_manager.proxies.redis import RedisProxy


QGC_MISSION_CMD_CHANNEL = "/petal/qgc_mission_adapter/cmd"
QGC_MISSION_ACK_CHANNEL = "/petal/qgc_mission_adapter/ack"


class MissionTranslationService:
    """Translates missions from MAVLink to LeafSDK format and handles Redis communication.
    
    Responsibilities:
    - Convert MAVLink waypoints to LeafSDK MissionPlan format
    - Publish missions to Redis
    - Handle ACKs from petal-leafsdk
    - Manage step-to-waypoint mapping
    - Write debug artifacts
    """
    
    def __init__(
        self,
        storage: MissionStorage,
        redis_proxy: Optional[RedisProxy],
        adapter_state: AdapterState,
        debug_dir: Optional[Path] = None
    ):
        """Initialize translation service.
        
        Args:
            storage: Mission storage instance
            redis_proxy: Redis proxy for communication
            adapter_state: Adapter state
            debug_dir: Directory for debug artifacts
        """
        self.storage = storage
        self.redis_proxy = redis_proxy
        self.vs = adapter_state
        self.debug_dir = debug_dir
        
        # Mapping between LeafSDK step IDs and QGC waypoint sequence numbers
        self.step_to_waypoint_map: Dict[str, int] = {}
        self.waypoint_to_step_map: Dict[int, str] = {}
        
        # Pending mission ACK tracking
        self._pending_mission_ack: Optional[Dict[str, Any]] = None
        
        # Setup ACK listener
        self._setup_ack_listener()
    
    def _setup_ack_listener(self) -> None:
        """Setup Redis listener for mission plan ACKs from petal-leafsdk."""
        if self.redis_proxy is None:
            logger.warning("Redis proxy not available; mission ACK listener not setup")
            return
        
        try:
            self.redis_proxy.subscribe(QGC_MISSION_ACK_CHANNEL, self._handle_ack_message)
            logger.info(f"Subscribed to mission ACK channel: {QGC_MISSION_ACK_CHANNEL}")
        except Exception as exc:
            logger.error(f"Failed to subscribe to ACK channel: {exc}")
    
    def translate_and_publish(
        self, 
        conn: MavlinkConnection,
        target_system: Optional[int] = None,
        target_component: Optional[int] = None
    ) -> None:
        """Translate mission to LeafSDK format and publish to Redis.
        
        The MAVLink ACK to QGC is deferred until we receive confirmation from
        petal-leafsdk via Redis.
        
        Args:
            conn: The MAVLink connection to send ACK on when Redis confirms
            target_system: Target system ID for ACK (GCS system ID)
            target_component: Target component ID for ACK (GCS component ID)
        """
        try:
            # Build PositionData from AdapterState
            pos = PositionData(
                # Vehicle GPS (from GLOBAL_POSITION_INT)
                vehicle_lat=self.vs.lat / 1e7,
                vehicle_lon=self.vs.lon / 1e7,
                vehicle_alt=self.vs.alt / 1000.0,
                vehicle_alt_relative=self.vs.relative_alt / 1000.0 if hasattr(self.vs, 'relative_alt') else 0.0,
                # Home GPS (from HOME_POSITION)
                home_lat=self.vs.home_lat / 1e7,
                home_lon=self.vs.home_lon / 1e7,
                home_alt=self.vs.home_alt / 1000.0,
                # Home local NED (from HOME_POSITION x,y,z)
                home_local_x=self.vs.home_local_x,
                home_local_y=self.vs.home_local_y,
                home_local_z=self.vs.home_local_z,
                # Vehicle local NED (from LOCAL_POSITION_NED)
                vehicle_local_x=self.vs.local_x,
                vehicle_local_y=self.vs.local_y,
                vehicle_local_z=self.vs.local_z,
            )
            pos.log_state()
            
            # Create translator and translate mission
            translator = MissionTranslator(pos, fly_to_mission_start=True)
            waypoints_dicts = self.storage.get_waypoints_as_dicts()
            mission_data = translator.translate(waypoints_dicts)
            
            # Create mapping between LeafSDK step IDs and QGC waypoint sequence numbers
            self.step_to_waypoint_map.clear()
            self.waypoint_to_step_map.clear()
            for node in mission_data["nodes"]:
                node_name = node["name"]
                # Extract sequence number from node name (e.g., "Takeoff0" -> 0, "Waypoint2" -> 2)
                for i, char in enumerate(node_name):
                    if char.isdigit():
                        seq = int(node_name[i:])
                        self.step_to_waypoint_map[node_name] = seq
                        self.waypoint_to_step_map[seq] = node_name
                        break
            
            logger.info(f"Created step-to-waypoint mapping: {self.step_to_waypoint_map}")
            
            # Only send if we have nodes
            if not mission_data["nodes"]:
                logger.warning("No valid nodes to upload to Petal server")
                self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR)
                return
            
            self._write_debug_artifacts(mission_data)
            logger.info(
                "Publishing mission to Petal server via Redis: %s nodes, %s edges",
                len(mission_data["nodes"]),
                len(mission_data["edges"]),
            )
            logger.debug(f"Mission data: {mission_data}")
            
            # Publish to Redis and store pending ACK info
            self._publish_to_redis(mission_data, conn, target_system, target_component)
        
        except Exception as e:
            logger.error(f"Failed to translate and publish mission: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR)
    
    def _publish_to_redis(
        self,
        mission_data: Dict[str, Any],
        conn: MavlinkConnection,
        target_system: Optional[int],
        target_component: Optional[int]
    ) -> None:
        """Publish mission plan to petal-leafsdk via Redis.
        
        Args:
            mission_data: The translated mission data
            conn: The MAVLink connection to store for later ACK
            target_system: Target system ID for ACK
            target_component: Target component ID for ACK
        """
        if self.redis_proxy is None:
            logger.warning("Redis proxy not available; sending error ACK to QGC")
            self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR)
            return
        
        message_id = f"mission-plan-{uuid.uuid4()}"
        redis_message = {
            "message_id": message_id,
            "command": "mission.plan",
            "payload": mission_data,
            "source": "petal-qgc-mission-server",
        }
        
        try:
            subscribers = self.redis_proxy.publish(
                channel=QGC_MISSION_CMD_CHANNEL,
                message=json.dumps(redis_message),
            )
            logger.info(
                "Published mission plan to Redis channel %s (message_id=%s, subscribers=%s)",
                QGC_MISSION_CMD_CHANNEL,
                message_id,
                subscribers,
            )
            
            if subscribers == 0:
                logger.error(
                    "No subscribers on channel %s - petal-leafsdk may not be running! "
                    "Sending error ACK to QGC.",
                    QGC_MISSION_CMD_CHANNEL,
                )
                self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR)
                return
            
            # Store pending ACK info
            self._pending_mission_ack = {
                "message_id": message_id,
                "conn": conn,
                "mission_type": self.storage.get_mission_type(),
                "target_system": target_system,
                "target_component": target_component,
            }
            logger.info(
                f"Waiting for ACK from petal-leafsdk (message_id={message_id}). "
                f"Will send ACK to system={target_system}, component={target_component}. "
                "QGC will not receive ACK until petal-leafsdk confirms."
            )
        
        except Exception as exc:
            logger.error("Failed to publish mission plan to Redis: %s", exc)
            self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR)
    
    def _handle_ack_message(self, channel: str, data: str) -> None:
        """Handle ACK messages from petal-leafsdk.
        
        Args:
            channel: The Redis channel
            data: The message data (JSON string)
        """
        try:
            payload = json.loads(data)
        except json.JSONDecodeError as exc:
            logger.warning(f"Invalid ACK payload: {exc}")
            return
        
        message_id = payload.get("message_id")
        status = payload.get("status")
        result = payload.get("result")
        error = payload.get("error")
        source = payload.get("source", "unknown")
        
        logger.info(
            f"Received ACK from {source}: message_id={message_id}, status={status}, "
            f"result={result}, error={error}"
        )
        
        # Check if this ACK matches our pending mission
        pending = self._pending_mission_ack
        if pending and pending.get("message_id") == message_id:
            conn = pending.get("conn")
            mission_type = pending.get("mission_type")
            target_system = pending.get("target_system")
            target_component = pending.get("target_component")
            
            # Clear pending state
            self._pending_mission_ack = None
            
            if status == "success":
                logger.info(f"Mission accepted by petal-leafsdk: {result}")
                if conn:
                    self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ACCEPTED, mission_type, target_system, target_component)
                    logger.info(f"Sent MISSION_ACK (ACCEPTED) to QGC system={target_system}, component={target_component}")
            else:
                error_msg = error or "Unknown error"
                logger.error(f"Mission REJECTED by petal-leafsdk: {error_msg}")
                if conn:
                    self._send_mission_ack(conn, mavutil.mavlink.MAV_MISSION_ERROR, mission_type, target_system, target_component)
                    logger.info(f"Sent MISSION_ACK (ERROR) to QGC system={target_system}, component={target_component} - petal-leafsdk rejected: {error_msg}")
        else:
            logger.debug(f"ACK for unknown/old message_id: {message_id}")
    
    def _send_mission_ack(
        self,
        conn: MavlinkConnection,
        result: int,
        mission_type: Optional[int] = None,
        target_system: Optional[int] = None,
        target_component: Optional[int] = None
    ) -> None:
        """Send mission acknowledgment to GCS.
        
        Args:
            conn: MAVLink connection
            result: Result code
            mission_type: Mission type (optional)
            target_system: Target system ID (optional, defaults to 0)
            target_component: Target component ID (optional, defaults to 0)
        """
        if mission_type is None:
            mission_type = self.storage.get_mission_type()
        
        # Use provided target IDs or default to 0
        target_sys = target_system if target_system is not None else 0
        target_comp = target_component if target_component is not None else 0
        
        logger.info(f"Sending MISSION_ACK: result={result}, type={mission_type}, to system={target_sys}, component={target_comp}")
        
        try:
            msg = conn.mav.mission_ack_encode(target_sys, target_comp, result, mission_type)
            logger.debug(f"MISSION_ACK message: {msg}")
            conn.send_message(msg)
        except TypeError:
            msg = conn.mav.mission_ack_encode(0, 0, result)
            if hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            conn.send_message(msg)
    
    def _write_debug_artifacts(self, mission_data: Dict[str, Any]) -> None:
        """Write debug artifacts for mission upload.
        
        Args:
            mission_data: The translated mission data
        """
        if self.debug_dir is None:
            return
        
        try:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            
            # Save raw MAVLink waypoints
            current_mission_file = self.debug_dir / "current_mission.json"
            current_mission_data = {
                "waypoints": self.storage.get_waypoints_as_dicts(),
                "count": self.storage.total(),
                "mission_type": self.storage.get_mission_type(),
            }
            current_mission_file.write_text(json.dumps(current_mission_data, indent=2), encoding="utf-8")
            
            # Save translated Petal mission
            mission_file = self.debug_dir / "last_petal_mission.json"
            mission_file.write_text(json.dumps(mission_data, indent=2), encoding="utf-8")
            
            # Save Redis message
            redis_message = {
                "message_id": "mission-plan-debug",
                "command": "mission.plan",
                "payload": mission_data,
                "source": "petal-qgc-mission-server",
            }
            redis_file = self.debug_dir / "last_petal_mission_message.json"
            redis_file.write_text(json.dumps(redis_message, indent=2), encoding="utf-8")
            
            # Generate curl script
            curl_script = f"""#!/bin/bash
# Auto-generated curl script for testing mission upload
# Mission ID: {mission_data.get('id', 'unknown')}
# Nodes: {len(mission_data.get('nodes', []))}
# Edges: {len(mission_data.get('edges', []))}

curl -X POST http://localhost:6379/publish \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(redis_message)}'
"""
            curl_file = self.debug_dir / "last_petal_mission_curl.sh"
            curl_file.write_text(curl_script, encoding="utf-8")
            curl_file.chmod(0o755)
            
            logger.info("Saved mission debug artifacts to %s", self.debug_dir)
        except Exception as exc:
            logger.warning(f"Failed to save mission debug artifacts: {exc}")
