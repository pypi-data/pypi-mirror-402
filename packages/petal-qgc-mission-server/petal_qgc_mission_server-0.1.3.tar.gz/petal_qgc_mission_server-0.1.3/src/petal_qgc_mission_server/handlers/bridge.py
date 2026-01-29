"""Mission progress bridge between LeafSDK (Redis) and MAVLink."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, Optional

from .. import logger

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..adapter_state import AdapterState
    from ..connection import MavlinkConnection
    from ..mission_handler import MissionProtocolHandler
    from petal_app_manager.proxies.redis import RedisProxy

QGC_PROGRESS_CHANNEL = "/petal/qgc_mission_adapter/progress"
QGC_MISSION_LEG_CHANNEL = "/petal/qgc_mission_adapter/mission_leg"


class MissionProgressBridge:
    """Bridge between LeafSDK (Redis) and MAVLink for mission progress updates."""
    
    def __init__(
        self,
        redis_proxy: Optional[RedisProxy],
        adapter_state: AdapterState,
        mission_handler: MissionProtocolHandler,
        conn: MavlinkConnection,
        send_statustext_fn: Any,
    ):
        """Initialize mission progress bridge.
        
        Args:
            redis_proxy: Redis proxy for subscribing to progress updates
            adapter_state: The adapter state
            mission_handler: The mission protocol handler
            conn: The MAVLink connection
            send_statustext_fn: Function to send status text messages
        """
        self.redis_proxy = redis_proxy
        self.vs = adapter_state
        self.mission = mission_handler
        self.conn = conn
        self._send_statustext = send_statustext_fn
        self._latest_progress: Optional[Dict[str, Any]] = None
        self._latest_mission_leg: Optional[Dict[str, Any]] = None
        self._mission_started = False
    
    def setup_listeners(self) -> None:
        """Set up Redis listeners for LeafSDK mission progress updates."""
        if self.redis_proxy is None:
            logger.warning("Redis proxy unavailable; mission progress updates will not be consumed")
            return
        try:
            self.redis_proxy.subscribe(QGC_PROGRESS_CHANNEL, self._handle_progress_message)
            self.redis_proxy.subscribe(QGC_MISSION_LEG_CHANNEL, self._handle_mission_leg_message)
            logger.info(
                "Subscribed to LeafSDK mission progress channels (%s, %s)",
                QGC_PROGRESS_CHANNEL,
                QGC_MISSION_LEG_CHANNEL,
            )
        except Exception as exc:
            logger.error("Failed to subscribe to LeafSDK mission progress channels: %s", exc)
    
    def _is_last_step(self, step_id: Optional[str]) -> bool:
        """Check if the given step is the last waypoint in the mission.
        
        Args:
            step_id: The step ID to check (e.g., "Waypoint2", "Land3")
            
        Returns:
            True if this is the last step in the mission, False otherwise
        """
        if not step_id:
            return False
        
        # Get the sequence number for this step
        seq = self.mission.step_to_waypoint_map.get(step_id)
        if seq is None:
            logger.debug(f"Step {step_id} not found in waypoint map")
            return False
        
        # Check if this is the last waypoint
        total_items = len(self.mission.waypoints)
        if total_items == 0:
            return False
        
        last_seq = total_items - 1
        is_last = (seq == last_seq)
        
        logger.debug(f"Step {step_id} seq={seq}, last_seq={last_seq}, is_last={is_last}")
        return is_last
    
    def _handle_progress_message(self, channel: str, data: str) -> None:
        """Handle mission progress messages from LeafSDK.
        
        Args:
            channel: The Redis channel
            data: The message data (JSON string)
        """
        try:
            payload = json.loads(data)
        except Exception as exc:
            logger.warning("Invalid mission progress payload on %s: %s", channel, exc)
            return

        status = payload.get("status") or {}
        mission_id = payload.get("mission_id")
        current_step = status.get("next_step_id") or status.get("step_id")
        state = status.get("state")
        
        logger.info(
            "LeafSDK mission progress mission=%s state=%s step=%s completed=%s",
            mission_id,
            state,
            current_step,
            status.get("step_completed"),
        )
        self._latest_progress = payload
        
        # Handle Mission Completion
        try:
            if state == "COMPLETED" or (state == "RUNNING" and status.get("step_completed") and self._is_last_step(current_step)):
                total_items = len(self.mission.waypoints)
                if total_items > 0:
                    last_seq = total_items - 1
                    
                    logger.info(f"Mission Complete! Sending completion signals to QGC")
                    
                    # 1. Send MISSION_ITEM_REACHED for the last waypoint
                    self.mission.send_mission_item_reached(self.conn, last_seq)
                    
                    # 2. Send MISSION_CURRENT with seq = total_items (indicates "past the end")
                    # This is the key signal that tells QGC the mission is complete
                    self.vs.current_mission_item = total_items
                    self.mission.send_mission_current(self.conn)
                    
                    # 3. Update mission state to IDLE
                    self.vs.mission_state = "IDLE"
                    
                    # 4. Send status text notification
                    self._send_statustext("Mission completed", mavutil.mavlink.MAV_SEVERITY_INFO)
                    
                    logger.info(f"Mission completion signals sent: ITEM_REACHED(seq={last_seq}), CURRENT(seq={total_items})")
        except Exception as exc:
            logger.error(f"Error handling mission completion for step {current_step}: {exc}", exc_info=True)
        
        # Send status text on mission start
        if state == "RUNNING" and not self._mission_started:
            self._mission_started = True
            self._send_statustext(f"Mission started: {mission_id}", mavutil.mavlink.MAV_SEVERITY_INFO)
        elif state in ("COMPLETED", "CANCELLED", "FAILED"):
            self._mission_started = False
    
    def _handle_mission_leg_message(self, channel: str, data: str) -> None:
        """Handle mission leg messages from LeafSDK.
        
        Args:
            channel: The Redis channel
            data: The message data (JSON string)
        """
        try:
            payload = json.loads(data)
        except Exception as exc:
            logger.warning("Invalid mission leg payload on %s: %s", channel, exc)
            return

        mission_id = payload.get("mission_id")
        current_step = payload.get("current_step_id")
        previous_step = payload.get("previous_step_id")
        state = payload.get("state")
        step_completed = payload.get("step_completed", False)
        
        logger.info(
            "LeafSDK mission leg mission=%s current=%s previous=%s state=%s",
            mission_id,
            current_step,
            previous_step,
            state,
        )
        self._latest_mission_leg = payload
        
        # Update current mission item and send to QGC
        if current_step:
            seq = self.mission.step_to_waypoint_map.get(current_step)
            if seq is not None:
                self.vs.current_mission_item = seq
                logger.info(f"Updated current mission item to seq {seq} (step {current_step})")
                self.mission.send_mission_current(self.conn)
            else:
                logger.debug(f"No waypoint mapping found for step {current_step}")
        
        # Send MISSION_ITEM_REACHED when previous step completes
        if step_completed and previous_step:
            prev_seq = self.mission.step_to_waypoint_map.get(previous_step)
            if prev_seq is not None:
                logger.info(f"Mission item {prev_seq} reached (step {previous_step})")
                self.mission.send_mission_item_reached(self.conn, prev_seq)
        
        # Update mission state based on LeafSDK state
        if state:
            if state == "RUNNING":
                self.vs.mission_state = "ACTIVE"
            elif state == "PAUSED":
                self.vs.mission_state = "PAUSED"
            elif state == "COMPLETED":
                self.vs.mission_state = "IDLE"
                self._send_statustext("Mission completed", mavutil.mavlink.MAV_SEVERITY_INFO)
            elif state == "CANCELLED":
                self.vs.mission_state = "IDLE"
                self._send_statustext("Mission cancelled", mavutil.mavlink.MAV_SEVERITY_WARNING)
            elif state == "FAILED":
                self.vs.mission_state = "IDLE"
                self._send_statustext("Mission failed", mavutil.mavlink.MAV_SEVERITY_ERROR)
