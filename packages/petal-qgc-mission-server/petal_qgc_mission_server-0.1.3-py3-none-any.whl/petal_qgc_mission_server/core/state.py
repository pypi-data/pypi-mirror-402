"""Domain models for vehicle and mission state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .geo import GeoPoint
from .ned import NEDPosition


class MissionPhase(Enum):
    """Mission execution phase."""
    IDLE = "idle"
    UPLOADING = "uploading"
    READY = "ready"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class HomePosition:
    """Home position with GPS and local NED."""
    gps: Optional[GeoPoint] = None
    local_ned: Optional[NEDPosition] = None
    is_set: bool = False
    
    def set_from_mavlink(self, lat: int, lon: int, alt: int, x: float, y: float, z: float) -> None:
        """Set from HOME_POSITION message."""
        self.gps = GeoPoint.from_mavlink(lat, lon, alt)
        self.local_ned = NEDPosition.from_xyz(x, y, z)
        self.is_set = True
    
    @property
    def lat_e7(self) -> int:
        return self.gps.lat_e7 if self.gps else 0
    
    @property
    def lon_e7(self) -> int:
        return self.gps.lon_e7 if self.gps else 0
    
    @property
    def alt_mm(self) -> int:
        return self.gps.alt_mm if self.gps else 0


@dataclass
class GPSOrigin:
    """GPS global origin (local NED frame origin)."""
    gps: Optional[GeoPoint] = None
    is_set: bool = False
    
    def set_from_mavlink(self, lat: int, lon: int, alt: int) -> None:
        """Set from GPS_GLOBAL_ORIGIN message."""
        self.gps = GeoPoint.from_mavlink(lat, lon, alt)
        self.is_set = True


@dataclass
class MissionState:
    """Mission execution state."""
    phase: MissionPhase = MissionPhase.IDLE
    current_item: int = 0
    total_items: int = 0
    taking_off: bool = False
    landing: bool = False
    returning: bool = False
    
    def reset(self) -> None:
        """Reset to idle state."""
        self.phase = MissionPhase.IDLE
        self.current_item = 0
        self.total_items = 0
        self.taking_off = False
        self.landing = False
        self.returning = False
