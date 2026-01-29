"""GPS message handler."""

from __future__ import annotations

from typing import TYPE_CHECKING
import time

from .. import logger

if TYPE_CHECKING:
    from ..adapter_state import AdapterState


class GPSHandler:
    """Handle GPS-related MAVLink messages."""
    
    def __init__(self, adapter_state: AdapterState):
        """Initialize GPS handler.
        
        Args:
            adapter_state: The adapter state to update
        """
        self.vs = adapter_state
        self._last_local_log_ts = 0.0
    
    def handle_global_position_int(self, msg) -> None:
        """Handle GLOBAL_POSITION_INT message.
        
        Args:
            msg: The GLOBAL_POSITION_INT message
        """
        self.vs.lat = msg.lat
        self.vs.lon = msg.lon
        self.vs.alt = msg.alt
        if hasattr(msg, 'relative_alt'):
            self.vs.relative_alt = msg.relative_alt
        self._update_home_if_needed()
    
    def handle_gps_raw_int(self, msg) -> None:
        """Handle GPS_RAW_INT message.
        
        Args:
            msg: The GPS_RAW_INT message
        """
        self.vs.lat = msg.lat
        self.vs.lon = msg.lon
        self.vs.alt = msg.alt
        self._update_home_if_needed()
    
    def handle_set_gps_global_origin(self, msg) -> None:
        """Handle SET_GPS_GLOBAL_ORIGIN message.
        
        Args:
            msg: The SET_GPS_GLOBAL_ORIGIN message
        """
        lat = getattr(msg, 'latitude', None)
        lon = getattr(msg, 'longitude', None)
        alt = getattr(msg, 'altitude', None)
        
        if lat is not None and lon is not None:
            self.vs.home_lat = lat
            self.vs.home_lon = lon
            if alt is not None:
                self.vs.home_alt = alt
            logger.info(
                f"GPS global origin set: lat={lat/1e7:.7f}, lon={lon/1e7:.7f}, "
                f"alt={alt/1000.0 if alt else 0:.2f}m"
            )
    
    def handle_home_position(self, msg) -> None:
        """Handle HOME_POSITION message.
        
        Args:
            msg: The HOME_POSITION message
        """
        # msg fields: latitude, longitude, altitude, x, y, z, q, approach_x, approach_y, approach_z
        prev_lat = self.vs.home_lat
        prev_lon = self.vs.home_lon
        prev_alt = self.vs.home_alt
        prev_x = self.vs.home_local_x
        prev_y = self.vs.home_local_y
        prev_z = self.vs.home_local_z

        def changed(a, b, scale=1.0, tol=0.1):
            return abs((a - b) / scale) > tol

        should_update = (
            not self.vs.home.is_set
            or changed(msg.latitude, prev_lat, scale=1e7)
            or changed(msg.longitude, prev_lon, scale=1e7)
            or changed(msg.altitude, prev_alt, scale=1000.0)
            or changed(msg.x, prev_x)
            or changed(msg.y, prev_y)
            or changed(msg.z, prev_z)
        )

        if should_update:
            self.vs.home_lat = msg.latitude
            self.vs.home_lon = msg.longitude
            self.vs.home_alt = msg.altitude
            self.vs.home_local_x = msg.x
            self.vs.home_local_y = msg.y
            self.vs.home_local_z = msg.z

            lat_deg = self.vs.home_lat / 1e7
            lon_deg = self.vs.home_lon / 1e7
            alt_m = self.vs.home_alt / 1000.0

            logger.info(
                f"Updated Home Position: "
                f"GPS=({lat_deg:.7f}, {lon_deg:.7f}, {alt_m:.2f}m), "
                f"Local NED=({self.vs.home_local_x:.2f}, {self.vs.home_local_y:.2f}, {self.vs.home_local_z:.2f})"
            )
    
    def handle_local_position_ned(self, msg) -> None:
        """Handle LOCAL_POSITION_NED message (msg ID 32).
        
        Updates current vehicle local position in NED frame:
        - x = North position (meters)
        - y = East position (meters)
        - z = Down position (meters, positive downward)
        
        Args:
            msg: The LOCAL_POSITION_NED message
        """
        self.vs.local_x = msg.x
        self.vs.local_y = msg.y
        self.vs.local_z = msg.z
        # Note: msg also has vx, vy, vz for velocities if needed

        now = time.monotonic()
        if now - self._last_local_log_ts >= 2.0:
            self._last_local_log_ts = now
            logger.debug(
                f"Vehicle local position NED=({self.vs.local_x:.2f}, {self.vs.local_y:.2f}, {self.vs.local_z:.2f})"
            )
    
    def handle_gps_global_origin(self, msg) -> None:
        """Handle GPS_GLOBAL_ORIGIN message (msg ID 49).
        
        This defines the (0,0,0) point of the Local NED frame.
        
        Args:
            msg: The GPS_GLOBAL_ORIGIN message
        """
        self.vs.gps_origin_lat = msg.latitude
        self.vs.gps_origin_lon = msg.longitude
        self.vs.gps_origin_alt = msg.altitude
        
        logger.info(
            f"Updated GPS Global Origin: "
            f"Lat={self.vs.gps_origin_lat/1e7:.7f}, Lon={self.vs.gps_origin_lon/1e7:.7f}, Alt={self.vs.gps_origin_alt/1000.0:.2f}m"
        )
    
    def _update_home_if_needed(self) -> None:
        """Update home position if not yet set."""
        if self.vs.home_lat == 0 and self.vs.home_lon == 0:
            self.vs.home_lat = self.vs.lat
            self.vs.home_lon = self.vs.lon
            self.vs.home_alt = self.vs.alt
            logger.info(
                f"Home position initialized from GPS: "
                f"lat={self.vs.home_lat/1e7:.7f}, lon={self.vs.home_lon/1e7:.7f}, "
                f"alt={self.vs.home_alt/1000.0:.2f}m"
            )
