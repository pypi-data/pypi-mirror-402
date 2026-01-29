"""Coordinate conversion between GPS and local NED."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from .geo import GeoPoint
from .ned import NEDPosition

EARTH_RADIUS_M = 6371000.0


@dataclass
class CoordinateConverter:
    """Converts between GPS and local NED coordinates."""
    origin: GeoPoint
    home: Optional[GeoPoint] = None
    
    def gps_to_ned(self, point: GeoPoint) -> NEDPosition:
        """Convert GPS to local NED."""
        dlat = point.lat_deg - self.origin.lat_deg
        dlon = point.lon_deg - self.origin.lon_deg
        
        north = dlat * (math.pi / 180.0) * EARTH_RADIUS_M
        east = dlon * (math.pi / 180.0) * EARTH_RADIUS_M * math.cos(math.radians(self.origin.lat_deg))
        down = self.origin.alt_m - point.alt_m
        
        return NEDPosition(north=north, east=east, down=down)
    
    def ned_to_gps(self, ned: NEDPosition) -> GeoPoint:
        """Convert local NED to GPS."""
        lat = self.origin.lat_deg + ned.north / EARTH_RADIUS_M * (180.0 / math.pi)
        lon = self.origin.lon_deg + ned.east / (EARTH_RADIUS_M * math.cos(math.radians(self.origin.lat_deg))) * (180.0 / math.pi)
        alt = self.origin.alt_m - ned.down
        
        return GeoPoint(lat_deg=lat, lon_deg=lon, alt_m=alt)
    
    def relative_to_msl(self, alt_relative: float) -> float:
        """Convert relative altitude to MSL."""
        if self.home is None:
            raise ValueError("Home required")
        return self.home.alt_m + alt_relative
    
    def msl_to_relative(self, alt_msl: float) -> float:
        """Convert MSL to relative altitude."""
        if self.home is None:
            raise ValueError("Home required")
        return alt_msl - self.home.alt_m
