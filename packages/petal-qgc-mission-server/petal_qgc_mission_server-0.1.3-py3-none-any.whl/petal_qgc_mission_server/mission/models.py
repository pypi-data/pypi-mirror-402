"""Data models for mission handling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Waypoint:
    """Type-safe waypoint representation.
    
    Replaces the Dict[str, Any] approach with a proper dataclass for:
    - Type safety
    - Better IDE support
    - Validation
    - Clear documentation
    """
    seq: int
    frame: int
    command: int
    current: int
    autocontinue: int
    param1: float
    param2: float
    param3: float
    param4: float
    x: Optional[int]  # Latitude * 1e7
    y: Optional[int]  # Longitude * 1e7
    z: float  # Altitude
    lat: Optional[float] = None  # Latitude in degrees
    lon: Optional[float] = None  # Longitude in degrees
    alt: float = 0.0  # Altitude (same as z)
    speed_change: bool = False  # True if this is a speed change command
    
    @classmethod
    def from_dict(cls, data: dict) -> Waypoint:
        """Create Waypoint from dictionary (for backwards compatibility).
        
        Args:
            data: Dictionary with waypoint data
            
        Returns:
            Waypoint instance
        """
        return cls(
            seq=data["seq"],
            frame=data["frame"],
            command=data["command"],
            current=data["current"],
            autocontinue=data["autocontinue"],
            param1=data["param1"],
            param2=data["param2"],
            param3=data["param3"],
            param4=data["param4"],
            x=data.get("x"),
            y=data.get("y"),
            z=data["z"],
            lat=data.get("lat"),
            lon=data.get("lon"),
            alt=data.get("alt", data["z"]),
            speed_change=data.get("speed_change", False),
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary (for backwards compatibility).
        
        Returns:
            Dictionary representation
        """
        return {
            "seq": self.seq,
            "frame": self.frame,
            "command": self.command,
            "current": self.current,
            "autocontinue": self.autocontinue,
            "param1": self.param1,
            "param2": self.param2,
            "param3": self.param3,
            "param4": self.param4,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "lat": self.lat,
            "lon": self.lon,
            "alt": self.alt,
            "speed_change": self.speed_change,
        }


@dataclass
class UploadState:
    """State tracking for mission upload from GCS.
    
    Encapsulates all state related to receiving a mission from QGC.
    """
    expected_seq: int = 0
    waypoint_count: int = 0
    partner_system: Optional[int] = None  # GCS system ID
    partner_component: Optional[int] = None  # GCS component ID
    mission_type: int = 0  # MAV_MISSION_TYPE_*
    active: bool = False
    request_attempts: dict[int, int] = field(default_factory=dict)
    duplicate_last_seq: int = 0
    
    def reset(self) -> None:
        """Reset upload state."""
        self.expected_seq = 0
        self.waypoint_count = 0
        self.partner_system = None
        self.partner_component = None
        self.active = False
        self.request_attempts.clear()
        self.duplicate_last_seq = 0
    
    def start_upload(
        self, 
        count: int, 
        mission_type: int,
        system: Optional[int] = None,
        component: Optional[int] = None
    ) -> None:
        """Start a new upload session.
        
        Args:
            count: Number of waypoints to expect
            mission_type: Mission type (MAV_MISSION_TYPE_*)
            system: Source system ID
            component: Source component ID
        """
        self.waypoint_count = count
        self.mission_type = mission_type
        self.partner_system = system
        self.partner_component = component
        self.expected_seq = 0
        self.active = True
        self.request_attempts.clear()
        self.duplicate_last_seq = 0


@dataclass
class DownloadState:
    """State tracking for mission download to GCS.
    
    Encapsulates all state related to sending a mission to QGC.
    """
    target_system: Optional[int] = None
    target_component: Optional[int] = None
    in_progress: bool = False
    pending_plan: bool = False  # Waiting to compute mission plan after download
    
    def reset(self) -> None:
        """Reset download state."""
        self.target_system = None
        self.target_component = None
        self.in_progress = False
        self.pending_plan = False
    
    def start_download(
        self,
        system: Optional[int] = None,
        component: Optional[int] = None
    ) -> None:
        """Start a new download session.
        
        Args:
            system: Target system ID
            component: Target component ID
        """
        self.target_system = system
        self.target_component = component
        self.in_progress = True


@dataclass
class EmptyMissionState:
    """State tracking for fence/rally (empty) mission uploads.
    
    These missions are received but discarded (not stored).
    """
    active: bool = False
    mission_type: int = 0
    expected_count: int = 0
    expected_seq: int = 0
    partner_system: Optional[int] = None
    partner_component: Optional[int] = None
    
    def reset(self) -> None:
        """Reset empty mission state."""
        self.active = False
        self.mission_type = 0
        self.expected_count = 0
        self.expected_seq = 0
        self.partner_system = None
        self.partner_component = None
    
    def start_upload(
        self,
        mission_type: int,
        count: int,
        system: Optional[int] = None,
        component: Optional[int] = None
    ) -> None:
        """Start empty mission upload.
        
        Args:
            mission_type: Mission type (fence/rally)
            count: Number of items to expect
            system: Source system ID
            component: Source component ID
        """
        self.active = True
        self.mission_type = mission_type
        self.expected_count = count
        self.expected_seq = 0
        self.partner_system = system
        self.partner_component = component
