"""Vehicle state for mission management."""

from __future__ import annotations

from . import logger
from .core import GeoPoint, NEDPosition, HomePosition, GPSOrigin, MissionState, MissionPhase

try:
    from pymavlink import mavutil
except ImportError as exc:
    raise RuntimeError("pymavlink must be installed") from exc


class AdapterState:
    """Mutable state for mission adapter.
    
    Uses domain models for grouped state:
    - home: HomePosition (GPS + local NED)
    - gps_origin: GPSOrigin (local frame origin)
    - mission: MissionState (phase + flags)
    
    Direct fields for frequently-accessed values (backwards compatible).
    """

    def __init__(self) -> None:
        # Position (MAVLink format: lat*1e7, lon*1e7, alt in mm)
        self.lat = 0
        self.lon = 0
        self.alt = 0
        self.relative_alt = 0
        
        # Home and origin (using domain models)
        self.home = HomePosition()
        self.gps_origin = GPSOrigin()
        
        # Local positions (meters, NED frame)
        self.local_x = 0.0
        self.local_y = 0.0
        self.local_z = 0.0
        
        # Status
        self.armed = False
        self.mode = "POSCTL"
        self.system_status = mavutil.mavlink.MAV_STATE_STANDBY
        self.custom_mode = 65536
        self.landed_state = mavutil.mavlink.MAV_LANDED_STATE_ON_GROUND
        
        # GPS quality
        self.gps_fix_type = 0
        self.satellites_visible = 0
        
        # Mission (using domain model)
        self.mission = MissionState()
        
        # Speed
        self.target_speed = 0.5
        
        # Flags
        self.goto_active = False
    
    # === Backwards-compatible home accessors ===
    @property
    def home_lat(self) -> int:
        return self.home.lat_e7
    
    @home_lat.setter
    def home_lat(self, value: int) -> None:
        if self.home.gps:
            self.home.gps = GeoPoint.from_mavlink(value, self.home.lon_e7, self.home.alt_mm)
        else:
            self.home.gps = GeoPoint.from_mavlink(value, 0, 0)
        self.home.is_set = True
    
    @property
    def home_lon(self) -> int:
        return self.home.lon_e7
    
    @home_lon.setter
    def home_lon(self, value: int) -> None:
        if self.home.gps:
            self.home.gps = GeoPoint.from_mavlink(self.home.lat_e7, value, self.home.alt_mm)
        else:
            self.home.gps = GeoPoint.from_mavlink(0, value, 0)
        self.home.is_set = True
    
    @property
    def home_alt(self) -> int:
        return self.home.alt_mm
    
    @home_alt.setter
    def home_alt(self, value: int) -> None:
        if self.home.gps:
            self.home.gps = GeoPoint.from_mavlink(self.home.lat_e7, self.home.lon_e7, value)
        else:
            self.home.gps = GeoPoint.from_mavlink(0, 0, value)
        self.home.is_set = True
    
    @property
    def home_local_x(self) -> float:
        return self.home.local_ned.north if self.home.local_ned else 0.0
    
    @home_local_x.setter
    def home_local_x(self, value: float) -> None:
        y = self.home.local_ned.east if self.home.local_ned else 0.0
        z = self.home.local_ned.down if self.home.local_ned else 0.0
        self.home.local_ned = NEDPosition(value, y, z)
    
    @property
    def home_local_y(self) -> float:
        return self.home.local_ned.east if self.home.local_ned else 0.0
    
    @home_local_y.setter
    def home_local_y(self, value: float) -> None:
        x = self.home.local_ned.north if self.home.local_ned else 0.0
        z = self.home.local_ned.down if self.home.local_ned else 0.0
        self.home.local_ned = NEDPosition(x, value, z)
    
    @property
    def home_local_z(self) -> float:
        return self.home.local_ned.down if self.home.local_ned else 0.0
    
    @home_local_z.setter
    def home_local_z(self, value: float) -> None:
        x = self.home.local_ned.north if self.home.local_ned else 0.0
        y = self.home.local_ned.east if self.home.local_ned else 0.0
        self.home.local_ned = NEDPosition(x, y, value)
    
    # === Backwards-compatible GPS origin accessors ===
    @property
    def gps_origin_lat(self) -> int:
        return self.gps_origin.gps.lat_e7 if self.gps_origin.gps else 0
    
    @gps_origin_lat.setter
    def gps_origin_lat(self, value: int) -> None:
        if self.gps_origin.gps:
            self.gps_origin.gps = GeoPoint.from_mavlink(value, self.gps_origin.gps.lon_e7, self.gps_origin.gps.alt_mm)
        else:
            self.gps_origin.gps = GeoPoint.from_mavlink(value, 0, 0)
        self.gps_origin.is_set = True
    
    @property
    def gps_origin_lon(self) -> int:
        return self.gps_origin.gps.lon_e7 if self.gps_origin.gps else 0
    
    @gps_origin_lon.setter
    def gps_origin_lon(self, value: int) -> None:
        if self.gps_origin.gps:
            self.gps_origin.gps = GeoPoint.from_mavlink(self.gps_origin.gps.lat_e7, value, self.gps_origin.gps.alt_mm)
        else:
            self.gps_origin.gps = GeoPoint.from_mavlink(0, value, 0)
        self.gps_origin.is_set = True
    
    @property
    def gps_origin_alt(self) -> int:
        return self.gps_origin.gps.alt_mm if self.gps_origin.gps else 0
    
    @gps_origin_alt.setter
    def gps_origin_alt(self, value: int) -> None:
        if self.gps_origin.gps:
            self.gps_origin.gps = GeoPoint.from_mavlink(self.gps_origin.gps.lat_e7, self.gps_origin.gps.lon_e7, value)
        else:
            self.gps_origin.gps = GeoPoint.from_mavlink(0, 0, value)
        self.gps_origin.is_set = True
    
    # === Backwards-compatible mission accessors ===
    @property
    def current_mission_item(self) -> int:
        return self.mission.current_item
    
    @current_mission_item.setter
    def current_mission_item(self, value: int) -> None:
        self.mission.current_item = value
    
    @property
    def mission_state(self) -> str:
        return self.mission.phase.value.upper()
    
    @mission_state.setter
    def mission_state(self, value: str) -> None:
        try:
            self.mission.phase = MissionPhase(value.lower())
        except ValueError:
            self.mission.phase = MissionPhase.IDLE
    
    @property
    def taking_off(self) -> bool:
        return self.mission.taking_off
    
    @taking_off.setter
    def taking_off(self, value: bool) -> None:
        self.mission.taking_off = value
    
    @property
    def returning(self) -> bool:
        return self.mission.returning
    
    @returning.setter
    def returning(self, value: bool) -> None:
        self.mission.returning = value
    
    @property
    def landing(self) -> bool:
        return self.mission.landing
    
    @landing.setter
    def landing(self, value: bool) -> None:
        self.mission.landing = value
