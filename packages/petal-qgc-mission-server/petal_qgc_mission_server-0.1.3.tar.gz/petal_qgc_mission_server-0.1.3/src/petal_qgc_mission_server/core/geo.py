"""GeoPoint value object for GPS coordinates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    """Immutable GPS coordinate (lat, lon, alt in standard units).
    
    - lat_deg: Latitude in degrees
    - lon_deg: Longitude in degrees  
    - alt_m: Altitude in meters MSL
    """
    lat_deg: float
    lon_deg: float
    alt_m: float = 0.0
    
    @classmethod
    def from_mavlink(cls, lat: int, lon: int, alt: int = 0) -> GeoPoint:
        """Create from MAVLink format (lat*1e7, lon*1e7, alt in mm)."""
        return cls(lat / 1e7, lon / 1e7, alt / 1000.0)
    
    @classmethod
    def from_mavlink_int(cls, x: int, y: int, z: float) -> GeoPoint:
        """Create from MISSION_ITEM_INT (x=lat*1e7, y=lon*1e7, z=alt in m)."""
        return cls(x / 1e7, y / 1e7, z)
    
    @property
    def lat_e7(self) -> int:
        """Latitude in degE7 (MAVLink format)."""
        return int(self.lat_deg * 1e7)
    
    @property
    def lon_e7(self) -> int:
        """Longitude in degE7 (MAVLink format)."""
        return int(self.lon_deg * 1e7)
    
    @property
    def alt_mm(self) -> int:
        """Altitude in mm (MAVLink format)."""
        return int(self.alt_m * 1000)
    
    def is_valid(self) -> bool:
        """Check if coordinates are non-zero."""
        return not (self.lat_deg == 0.0 and self.lon_deg == 0.0)
    
    def __str__(self) -> str:
        return f"({self.lat_deg:.7f}, {self.lon_deg:.7f}, {self.alt_m:.1f}m)"
