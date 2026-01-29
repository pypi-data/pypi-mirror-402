"""MAVLink message helpers for mission protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .. import logger

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc

if TYPE_CHECKING:
    from ..connection import MavlinkConnection


class MavlinkMessageBuilder:
    """Helper class for building MAVLink messages with version compatibility.
    
    Handles the try/except pattern for MAVLink message encoding across different
    pymavlink versions, eliminating code duplication.
    """
    
    @staticmethod
    def mission_request_int(
        conn: MavlinkConnection,
        target_system: int,
        target_component: int,
        seq: int,
        mission_type: Optional[int] = None
    ) -> bool:
        """Send MISSION_REQUEST_INT message.
        
        Args:
            conn: MAVLink connection
            target_system: Target system ID
            target_component: Target component ID
            seq: Sequence number to request
            mission_type: Mission type (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            # Try with mission_type parameter (newer MAVLink)
            msg = conn.mav.mission_request_int_encode(
                target_system,
                target_component,
                seq,
                mission_type or 0
            )
            conn.send_message(msg)
            return True
        except TypeError:
            # Fallback for older MAVLink versions
            try:
                msg = conn.mav.mission_request_int_encode(
                    target_system,
                    target_component,
                    seq
                )
                if mission_type is not None and hasattr(msg, "mission_type"):
                    msg.mission_type = mission_type
                conn.send_message(msg)
                return True
            except Exception as exc:
                logger.error(f"Failed to send MISSION_REQUEST_INT: {exc}")
                return False
    
    @staticmethod
    def mission_count(
        conn: MavlinkConnection,
        target_system: int,
        target_component: int,
        count: int,
        mission_type: Optional[int] = None
    ) -> bool:
        """Send MISSION_COUNT message.
        
        Args:
            conn: MAVLink connection
            target_system: Target system ID
            target_component: Target component ID
            count: Number of waypoints
            mission_type: Mission type (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            msg = conn.mav.mission_count_encode(
                target_system,
                target_component,
                count,
                mission_type or 0
            )
            conn.send_message(msg)
            return True
        except TypeError:
            msg = conn.mav.mission_count_encode(target_system, target_component, count)
            if mission_type is not None and hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            conn.send_message(msg)
            return True
    
    @staticmethod
    def mission_ack(
        conn: MavlinkConnection,
        target_system: int,
        target_component: int,
        result: int,
        mission_type: Optional[int] = None
    ) -> bool:
        """Send MISSION_ACK message.
        
        Args:
            conn: MAVLink connection
            target_system: Target system ID
            target_component: Target component ID
            result: Result code (MAV_MISSION_ACCEPTED, MAV_MISSION_ERROR, etc.)
            mission_type: Mission type (optional)
            
        Returns:
            True if sent successfully
        """
        logger.info(
            f"Sending MISSION_ACK: result={result}, type={mission_type or 0}, "
            f"to system={target_system}, component={target_component}"
        )
        
        try:
            msg = conn.mav.mission_ack_encode(
                target_system,
                target_component,
                result,
                mission_type or 0
            )
            logger.debug(f"MISSION_ACK message: {msg}")
            conn.send_message(msg)
            return True
        except TypeError:
            msg = conn.mav.mission_ack_encode(target_system, target_component, result)
            if mission_type is not None and hasattr(msg, "mission_type"):
                msg.mission_type = mission_type
            logger.debug(f"MISSION_ACK message (fallback): {msg}")
            conn.send_message(msg)
            return True
    
    @staticmethod
    def mission_item_int(
        conn: MavlinkConnection,
        target_system: int,
        target_component: int,
        seq: int,
        frame: int,
        command: int,
        current: int,
        autocontinue: int,
        param1: float,
        param2: float,
        param3: float,
        param4: float,
        x: int,  # latitude * 1e7
        y: int,  # longitude * 1e7
        z: float,  # altitude
        mission_type: Optional[int] = None
    ) -> bool:
        """Send MISSION_ITEM_INT message.
        
        Args:
            conn: MAVLink connection
            target_system: Target system ID
            target_component: Target component ID
            seq: Sequence number
            frame: Frame type
            command: Command ID
            current: Current waypoint flag
            autocontinue: Autocontinue flag
            param1-4: Command parameters
            x: Latitude * 1e7
            y: Longitude * 1e7
            z: Altitude
            mission_type: Mission type (optional)
            
        Returns:
            True if sent successfully
        """
        try:
            msg = conn.mav.mission_item_int_encode(
                target_system,
                target_component,
                seq,
                frame,
                command,
                current,
                autocontinue,
                param1,
                param2,
                param3,
                param4,
                x,
                y,
                z,
                mission_type or 0
            )
            conn.send_message(msg)
            return True
        except TypeError:
            # Fallback to MISSION_ITEM (non-INT) for older MAVLink
            try:
                lat = x / 1e7
                lon = y / 1e7
                msg = conn.mav.mission_item_encode(
                    target_system,
                    target_component,
                    seq,
                    frame,
                    command,
                    current,
                    autocontinue,
                    param1,
                    param2,
                    param3,
                    param4,
                    lat,
                    lon,
                    z
                )
                conn.send_message(msg)
                return True
            except Exception as exc:
                logger.error(f"Failed to send MISSION_ITEM: {exc}")
                return False
    
    @staticmethod
    def mission_current(conn: MavlinkConnection, seq: int) -> bool:
        """Send MISSION_CURRENT message.
        
        Args:
            conn: MAVLink connection
            seq: Current mission item sequence number
            
        Returns:
            True if sent successfully
        """
        try:
            msg = conn.mav.mission_current_encode(seq)
            conn.send_message(msg)
            return True
        except Exception as exc:
            logger.error(f"Failed to send MISSION_CURRENT: {exc}")
            return False
    
    @staticmethod
    def mission_item_reached(conn: MavlinkConnection, seq: int) -> bool:
        """Send MISSION_ITEM_REACHED message.
        
        Args:
            conn: MAVLink connection
            seq: Sequence number of reached waypoint
            
        Returns:
            True if sent successfully
        """
        try:
            msg = conn.mav.mission_item_reached_encode(seq)
            conn.send_message(msg)
            return True
        except Exception as exc:
            logger.error(f"Failed to send MISSION_ITEM_REACHED: {exc}")
            return False
