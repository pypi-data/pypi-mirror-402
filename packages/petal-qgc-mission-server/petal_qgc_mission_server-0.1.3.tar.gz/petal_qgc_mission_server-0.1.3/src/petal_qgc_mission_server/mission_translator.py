"""Mission translation logic (MAVLink -> Petal).

This module provides coordinate conversion and mission translation from 
MAVLink waypoints to Petal mission graphs.

Coordinate Frames:
- GPS: lat/lon in degrees, alt in meters
- NED: North-East-Down (x=North, y=East, z=Down positive downward)
- ENU: East-North-Up (x=East, y=North, z=Up positive upward)

The origin for local coordinates is derived from HOME_POSITION:
- Origin GPS = Home GPS location
- Origin Local = (0, 0, 0) by definition
- Home Local NED from HOME_POSITION message tells us home's offset from origin
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from . import logger

try:
    from pymavlink import mavutil
except ImportError:
    mavutil = None


# =============================================================================
# CONSTANTS
# =============================================================================

METERS_PER_DEGREE_LAT = 111320.0  # Approximate meters per degree latitude
MAX_FLAT_EARTH_DISTANCE = 20000.0  # 20km - flat-earth approximation limit


# =============================================================================
# COORDINATE CONVERSION HELPERS (Pure Functions)
# =============================================================================

def ned_to_enu(ned: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert NED to ENU coordinates.
    
    NED: (North, East, Down) - z positive downward
    ENU: (East, North, Up) - z positive upward
    
    Args:
        ned: (x_north, y_east, z_down) in meters
        
    Returns:
        (east, north, up) in meters
    """
    x_north, y_east, z_down = ned
    return (y_east, x_north, -z_down)


def enu_to_ned(enu: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert ENU to NED coordinates.
    
    ENU: (East, North, Up) - z positive upward
    NED: (North, East, Down) - z positive downward
    
    Args:
        enu: (east, north, up) in meters
        
    Returns:
        (x_north, y_east, z_down) in meters
    """
    east, north, up = enu
    return (north, east, -up)


def gps_to_local_enu(
    lat: float, 
    lon: float, 
    origin_lat: float, 
    origin_lon: float
) -> Tuple[float, float]:
    """Convert GPS to local ENU offset from origin.
    
    Uses flat-earth approximation. Valid for distances < 20km.
    
    Args:
        lat: Target latitude (degrees)
        lon: Target longitude (degrees)
        origin_lat: Origin latitude (degrees)
        origin_lon: Origin longitude (degrees)
        
    Returns:
        (east_meters, north_meters) offset from origin
    """
    dlat = lat - origin_lat
    dlon = lon - origin_lon
    
    north = dlat * METERS_PER_DEGREE_LAT
    east = dlon * METERS_PER_DEGREE_LAT * math.cos(math.radians(origin_lat))
    
    return (east, north)


def local_enu_to_gps(
    east: float,
    north: float,
    origin_lat: float,
    origin_lon: float
) -> Tuple[float, float]:
    """Convert local ENU offset to GPS coordinates.
    
    Inverse of gps_to_local_enu. Uses flat-earth approximation.
    
    Args:
        east: East offset from origin (meters)
        north: North offset from origin (meters)
        origin_lat: Origin latitude (degrees)
        origin_lon: Origin longitude (degrees)
        
    Returns:
        (latitude, longitude) in degrees
    """
    dlat = north / METERS_PER_DEGREE_LAT
    dlon = east / (METERS_PER_DEGREE_LAT * math.cos(math.radians(origin_lat)))
    
    return (origin_lat + dlat, origin_lon + dlon)


def calculate_yaw_to_target_ENU(
    from_east: float,
    from_north: float,
    to_east: float,
    to_north: float
) -> float:
    """Calculate yaw angle from one point to another in ENU frame.
    
    ENU Yaw Convention:
    - 0° = East (+X direction)
    - 90° = North (+Y direction)
    - 180° = West (-X direction)
    - -90° (or 270°) = South (-Y direction)
    
    Args:
        from_east, from_north: Start position (meters)
        to_east, to_north: Target position (meters)
        
    Returns:
        Yaw angle in degrees using ENU convention.
    """
    delta_east = to_east - from_east
    delta_north = to_north - from_north
    
    if abs(delta_east) < 0.01 and abs(delta_north) < 0.01:
        return 0.0
    
    # ENU yaw: atan2(north, east) gives 0°=East, 90°=North
    return math.degrees(math.atan2(delta_north, delta_east))

def calculate_yaw_to_target( #NED default
    from_east: float,
    from_north: float,
    to_east: float,
    to_north: float
) -> float:
    """Calculate yaw angle from one point to another in NED frame.
    
    NED Yaw Convention:
    - 0° = North (+Y direction in ENU, +X in NED)
    - 90° = East (+X direction in ENU, +Y in NED)
    - 180° = South (-Y direction in ENU)
    - -90° (or 270°) = West (-X direction in ENU)
    
    Args:
        from_east, from_north: Start position (meters)
        to_east, to_north: Target position (meters)
        
    Returns:
        Yaw angle in degrees using NED convention.
    """
    delta_east = to_east - from_east
    delta_north = to_north - from_north
    
    if abs(delta_east) < 0.01 and abs(delta_north) < 0.01:
        return 0.0
    
    # NED yaw: atan2(east, north) gives 0°=North, 90°=East
    return math.degrees(math.atan2(delta_east, delta_north))

# =============================================================================
# POSITION DATA STORAGE
# =============================================================================

@dataclass
class PositionData:
    """Raw position data from MAVLink messages.
    
    This class stores raw values as received. No conversions.
    All GPS values in degrees, all local values in meters.
    """
    # Current vehicle GPS (from GLOBAL_POSITION_INT)
    vehicle_lat: float = 0.0  # degrees
    vehicle_lon: float = 0.0  # degrees
    vehicle_alt: float = 0.0  # meters MSL
    vehicle_alt_relative: float = 0.0  # meters above home
    
    # Home GPS (from HOME_POSITION)
    home_lat: float = 0.0  # degrees
    home_lon: float = 0.0  # degrees
    home_alt: float = 0.0  # meters MSL
    
    # Home local NED (from HOME_POSITION x,y,z)
    # These are home's position relative to the local frame origin
    home_local_x: float = 0.0  # North (meters)
    home_local_y: float = 0.0  # East (meters)
    home_local_z: float = 0.0  # Down (meters, positive = below origin)
    
    # Current vehicle local NED (from LOCAL_POSITION_NED)
    vehicle_local_x: float = 0.0  # North (meters)
    vehicle_local_y: float = 0.0  # East (meters)
    vehicle_local_z: float = 0.0  # Down (meters)
    
    def log_state(self) -> None:
        """Log current position data state."""
        logger.info("=" * 60)
        logger.info("PositionData State:")
        logger.info(f"  Vehicle GPS: ({self.vehicle_lat:.7f}, {self.vehicle_lon:.7f}, {self.vehicle_alt:.1f}m)")
        logger.info(f"  Home GPS: ({self.home_lat:.7f}, {self.home_lon:.7f}, {self.home_alt:.1f}m)")
        logger.info(f"  Home Local NED: ({self.home_local_x:.2f}, {self.home_local_y:.2f}, {self.home_local_z:.2f})")
        logger.info(f"  Vehicle Local NED: ({self.vehicle_local_x:.2f}, {self.vehicle_local_y:.2f}, {self.vehicle_local_z:.2f})")
        logger.info("=" * 60)


# =============================================================================
# ORIGIN CALCULATOR
# =============================================================================

@dataclass
class LocalFrameOrigin:
    """Defines the origin (0,0,0) of the local coordinate frame.
    
    The origin is derived from HOME_POSITION:
    - Origin GPS = Home GPS minus Home Local offset (converted to GPS)
    - If Home Local is (0,0,0), then Origin = Home
    
    This approach does NOT rely on GPS_GLOBAL_ORIGIN message.
    """
    lat: float = 0.0  # Origin latitude (degrees)
    lon: float = 0.0  # Origin longitude (degrees)
    alt: float = 0.0  # Origin altitude (meters MSL)
    is_valid: bool = False
    
    @classmethod
    def from_home_position(
        cls,
        home_lat: float,
        home_lon: float,
        home_alt: float,
        home_local_x: float,
        home_local_y: float,
        home_local_z: float
    ) -> "LocalFrameOrigin":
        """Calculate origin from HOME_POSITION data.
        
        The HOME_POSITION message gives us:
        - home_lat/lon/alt: GPS location of home
        - home_local_x/y/z: Home's position in local NED frame
        
        If home is at local (10, 5, -2) NED, it means:
        - Home is 10m North, 5m East, 2m Up from origin
        
        So origin GPS = home GPS - local offset (converted to GPS)
        
        Args:
            home_lat, home_lon, home_alt: Home GPS (degrees, meters)
            home_local_x, home_local_y, home_local_z: Home local NED (meters)
            
        Returns:
            LocalFrameOrigin with calculated origin position
        """
        if home_lat == 0.0 and home_lon == 0.0:
            logger.warning("Cannot calculate origin: Home GPS is (0, 0)")
            return cls(is_valid=False)
        
        # Convert home local NED to offset in GPS terms
        # Home is at (north, east) meters from origin
        # So origin is home GPS minus that offset
        home_north = home_local_x
        home_east = home_local_y
        
        # Convert local offset to GPS delta
        dlat = home_north / METERS_PER_DEGREE_LAT
        dlon = home_east / (METERS_PER_DEGREE_LAT * math.cos(math.radians(home_lat)))
        
        # Origin GPS = Home GPS - offset
        origin_lat = home_lat - dlat
        origin_lon = home_lon - dlon
        # For altitude: origin is at z=0, home is at -home_local_z up from origin
        origin_alt = home_alt + home_local_z  # home_local_z is Down, so + gives lower alt
        
        logger.info(f"Origin calculated from HOME_POSITION:")
        logger.info(f"  Home GPS: ({home_lat:.7f}, {home_lon:.7f})")
        logger.info(f"  Home Local NED: ({home_local_x:.2f}, {home_local_y:.2f}, {home_local_z:.2f})")
        logger.info(f"  => Origin GPS: ({origin_lat:.7f}, {origin_lon:.7f}, {origin_alt:.1f}m)")
        
        return cls(
            lat=origin_lat,
            lon=origin_lon,
            alt=origin_alt,
            is_valid=True
        )


# =============================================================================
# COORDINATE CONVERTER
# =============================================================================

class CoordinateConverter:
    """Converts between GPS and local ENU coordinates.
    
    Usage:
        1. Create with origin
        2. Call gps_to_enu() or enu_to_gps() as needed
    """
    
    def __init__(self, origin: LocalFrameOrigin):
        """Initialize converter with origin.
        
        Args:
            origin: The local frame origin
        """
        if not origin.is_valid:
            raise ValueError("Cannot create converter with invalid origin")
        
        self.origin = origin
        logger.info(f"CoordinateConverter initialized with origin: ({origin.lat:.7f}, {origin.lon:.7f})")
    
    def gps_to_enu(self, lat: float, lon: float, alt: float) -> Tuple[float, float, float]:
        """Convert GPS to local ENU.
        
        Args:
            lat: Latitude (degrees)
            lon: Longitude (degrees)
            alt: Altitude MSL (meters)
            
        Returns:
            (east, north, up) in meters relative to origin
        """
        east, north = gps_to_local_enu(lat, lon, self.origin.lat, self.origin.lon)
        up = alt - self.origin.alt
        return (east, north, up)
    
    def enu_to_gps(self, east: float, north: float, up: float) -> Tuple[float, float, float]:
        """Convert local ENU to GPS.
        
        Args:
            east: East position (meters)
            north: North position (meters)  
            up: Up position (meters)
            
        Returns:
            (lat, lon, alt) in degrees and meters MSL
        """
        lat, lon = local_enu_to_gps(east, north, self.origin.lat, self.origin.lon)
        alt = up + self.origin.alt
        return (lat, lon, alt)
    
    def ned_to_enu(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Convert NED to ENU. Convenience wrapper.
        
        Args:
            x: North (meters)
            y: East (meters)
            z: Down (meters, positive downward)
            
        Returns:
            (east, north, up) in meters
        """
        return ned_to_enu((x, y, z))
    
    def enu_to_ned(self, east: float, north: float, up: float) -> Tuple[float, float, float]:
        """Convert ENU to NED. Convenience wrapper.
        
        Args:
            east: East (meters)
            north: North (meters)
            up: Up (meters, positive upward)
            
        Returns:
            (x_north, y_east, z_down) in meters
        """
        return enu_to_ned((east, north, up))


from leafsdk.core.mission.mission_plan import MissionPlan
from leafsdk.core.mission.mission_plan_step import Takeoff, GotoLocalPosition, Wait, Land

# =============================================================================
# MISSION TRANSLATOR (New Implementation)
# =============================================================================

class MissionTranslator:
    """Translates MAVLink waypoints to Petal mission graph.
    
    This is the main class for mission translation.
    
    Usage:
        1. Create PositionData and populate from MAVLink messages
        2. Create MissionTranslator with PositionData
        3. Call translate(waypoints) to get mission graph
    """
    
    def __init__(self, position_data: PositionData, fly_to_mission_start: bool = True):
        """Initialize translator.
        
        Args:
            position_data: Current position data from MAVLink
            fly_to_mission_start: If True, add waypoint to fly to mission start location
        """
        self.pos = position_data
        self.fly_to_mission_start = fly_to_mission_start
        
        # Calculate origin from home position
        self.origin = LocalFrameOrigin.from_home_position(
            home_lat=position_data.home_lat,
            home_lon=position_data.home_lon,
            home_alt=position_data.home_alt,
            home_local_x=position_data.home_local_x,
            home_local_y=position_data.home_local_y,
            home_local_z=position_data.home_local_z
        )
        
        if not self.origin.is_valid:
            raise ValueError("Cannot translate mission: Origin could not be calculated. Check HOME_POSITION data.")
        
        # Create converter
        self.converter = CoordinateConverter(self.origin)
        
        # Calculate key positions in ENU
        self.home_enu = self.converter.ned_to_enu(
            position_data.home_local_x,
            position_data.home_local_y,
            position_data.home_local_z
        )
        
        self.vehicle_enu = self.converter.ned_to_enu(
            position_data.vehicle_local_x,
            position_data.vehicle_local_y,
            position_data.vehicle_local_z
        )
        
        logger.info("MissionTranslator initialized:")
        logger.info(f"  Home ENU: ({self.home_enu[0]:.2f}, {self.home_enu[1]:.2f}, {self.home_enu[2]:.2f})")
        logger.info(f"  Vehicle ENU: ({self.vehicle_enu[0]:.2f}, {self.vehicle_enu[1]:.2f}, {self.vehicle_enu[2]:.2f})")
    
    def waypoint_gps_to_enu(self, lat: float, lon: float, alt_relative: float) -> Tuple[float, float, float]:
        """Convert waypoint GPS to ENU.
        
        Waypoint altitude is typically relative to home.
        
        Args:
            lat: Waypoint latitude (degrees)
            lon: Waypoint longitude (degrees)
            alt_relative: Altitude relative to home (meters)
            
        Returns:
            (east, north, up) in meters
        """
        # Get horizontal position from GPS
        east, north = gps_to_local_enu(lat, lon, self.origin.lat, self.origin.lon)
        
        # Altitude: waypoint alt is relative to home
        # up = home_up + alt_relative
        up = self.home_enu[2] + alt_relative
        
        return (east, north, up)
    
    def translate(self, waypoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert MAVLink waypoints to Petal mission graph.
        
        Args:
            waypoints: List of normalized waypoint dicts from MAVLink
            
        Returns:
            Mission graph dict with 'id', 'nodes', 'edges'
        """
        mission_plan = MissionPlan(name="main")
        
        current_enu = list(self.vehicle_enu)  # Track position as [E, N, U]
        current_speed = 0.5
        
        # MAVLink command IDs
        CMD_TAKEOFF = getattr(mavutil.mavlink, "MAV_CMD_NAV_TAKEOFF", 22) if mavutil else 22
        CMD_WAYPOINT = getattr(mavutil.mavlink, "MAV_CMD_NAV_WAYPOINT", 16) if mavutil else 16
        CMD_LAND = getattr(mavutil.mavlink, "MAV_CMD_NAV_LAND", 21) if mavutil else 21
        CMD_RTL = getattr(mavutil.mavlink, "MAV_CMD_NAV_RETURN_TO_LAUNCH", 20) if mavutil else 20
        CMD_SPEED = getattr(mavutil.mavlink, "MAV_CMD_DO_CHANGE_SPEED", 178) if mavutil else 178
        
        for wp in waypoints:
            if not wp:
                continue
                
            cmd = wp.get("command")
            seq = wp["seq"]
            
            # Handle speed change (no node created)
            if cmd == CMD_SPEED or wp.get("speed_change"):
                speed = wp.get("param2", 0.5)
                if speed > 0:
                    current_speed = float(speed)
                    logger.info(f"[Seq {seq}] Speed set to {current_speed:.1f} m/s")
                continue
            
            # Handle Takeoff
            if cmd == CMD_TAKEOFF:
                node_name = f"Takeoff{seq}"
                alt = float(wp.get("alt", 5.0))
                
                # Create Takeoff node
                mission_plan.add(node_name, Takeoff(alt=alt))
                
                # If mission has explicit takeoff location, fly there
                lat, lon = wp.get("lat"), wp.get("lon")
                if self.fly_to_mission_start and lat and lon and lat != 0 and lon != 0:
                    target = self.waypoint_gps_to_enu(lat, lon, alt)
                    
                    # Yaw Handling:
                    # 1. If param4 (Yaw) is provided and NOT NaN, use it (Explicit Yaw).
                    # 2. If param4 is NaN or missing, calculate yaw to face the target (Dynamic Yaw).
                    explicit_yaw = wp.get("param4")
                    if explicit_yaw is not None and not (isinstance(explicit_yaw, float) and math.isnan(explicit_yaw)):
                        yaw = float(explicit_yaw)
                        logger.info(f"[Seq {seq}] Takeoff: Using explicit yaw {yaw}°")
                    else:
                        yaw = calculate_yaw_to_target_ENU(current_enu[0], current_enu[1], target[0], target[1])
                        logger.info(f"[Seq {seq}] Takeoff: Calculated dynamic yaw {yaw:.1f}° to target")
                    
                    goto_name = f"GotoStart{seq}"
                    mission_plan.add(goto_name, GotoLocalPosition(
                        waypoints=[list(target)],
                        yaws_deg=[yaw],
                        speed=[current_speed],
                        yaw_speed="sync"
                    ))
                    
                    current_enu = list(target)
                    logger.info(f"[Seq {seq}] Takeoff + GotoStart: ENU=({target[0]:.1f}, {target[1]:.1f}, {target[2]:.1f})")
                    continue
                
                # Takeoff at home
                current_enu[2] = self.home_enu[2] + alt
                logger.info(f"[Seq {seq}] Takeoff at home, alt={alt}m")
                continue
            
            # Handle Waypoint
            if cmd == CMD_WAYPOINT:
                lat, lon = wp.get("lat"), wp.get("lon")
                if not lat or not lon:
                    logger.warning(f"[Seq {seq}] Waypoint missing GPS, skipped")
                    continue
                
                alt = float(wp.get("alt", 5.0))
                hold = float(wp.get("param1", 0.0))
                explicit_yaw = wp.get("param4")
                
                target = self.waypoint_gps_to_enu(lat, lon, alt)
                
                # Yaw Handling:
                # 1. If param4 (Yaw) is provided and NOT NaN, use it (Explicit Yaw).
                # 2. If param4 is NaN or missing, calculate yaw to face the target (Dynamic Yaw).
                if explicit_yaw is not None and not (isinstance(explicit_yaw, float) and math.isnan(explicit_yaw)):
                    yaw = float(explicit_yaw)
                    logger.info(f"[Seq {seq}] Waypoint: Using explicit yaw {yaw}°")
                else:
                    yaw = calculate_yaw_to_target_ENU(current_enu[0], current_enu[1], target[0], target[1])
                    logger.info(f"[Seq {seq}] Waypoint: Calculated dynamic yaw {yaw:.1f}° to target")
                
                node_name = f"Waypoint{seq}"
                mission_plan.add(node_name, GotoLocalPosition(
                    waypoints=[list(target)],
                    yaws_deg=[yaw],
                    speed=[current_speed],
                    yaw_speed="sync"
                ))
                
                current_enu = list(target)
                logger.info(f"[Seq {seq}] Waypoint: ENU=({target[0]:.1f}, {target[1]:.1f}, {target[2]:.1f}), yaw={yaw:.1f}°")
                
                # Add Wait node if hold time specified
                if hold > 0:
                    wait_name = f"Wait{seq}"
                    mission_plan.add(wait_name, Wait(duration=hold))
                
                continue
            
            # Handle Land
            if cmd == CMD_LAND:
                lat, lon = wp.get("lat"), wp.get("lon")
                
                # Land at specific location
                if lat and lon and lat != 0 and lon != 0:
                    alt = float(wp.get("alt", 0.0))
                    target = self.waypoint_gps_to_enu(lat, lon, alt)
                    
                    # Yaw Handling:
                    # 1. If param4 (Yaw) is provided and NOT NaN, use it (Explicit Yaw).
                    # 2. If param4 is NaN or missing, calculate yaw to face the target (Dynamic Yaw).
                    explicit_yaw = wp.get("param4")
                    if explicit_yaw is not None and not (isinstance(explicit_yaw, float) and math.isnan(explicit_yaw)):
                        yaw = float(explicit_yaw)
                        logger.info(f"[Seq {seq}] Land: Using explicit yaw {yaw}°")
                    else:
                        yaw = calculate_yaw_to_target_ENU(current_enu[0], current_enu[1], target[0], target[1])
                        logger.info(f"[Seq {seq}] Land: Calculated dynamic yaw {yaw:.1f}° to target")
                    
                    goto_name = f"GotoLand{seq}"
                    mission_plan.add(goto_name, GotoLocalPosition(
                        waypoints=[list(target)],
                        yaws_deg=[yaw],
                        speed=[0.3],
                        yaw_speed="sync"
                    ))
                    current_enu = list(target)
                    
                    land_name = f"Land{seq}"
                    mission_plan.add(land_name, Land())
                    logger.info(f"[Seq {seq}] Land at ENU=({target[0]:.1f}, {target[1]:.1f})")
                else:
                    # Land at current position
                    land_name = f"Land{seq}"
                    mission_plan.add(land_name, Land())
                    logger.info(f"[Seq {seq}] Land at current position")
                
                continue
            
            # Handle RTL
            if cmd == CMD_RTL:
                # Go to home at current altitude, then land
                target = (self.home_enu[0], self.home_enu[1], current_enu[2])
                yaw = calculate_yaw_to_target_ENU(current_enu[0], current_enu[1], target[0], target[1])
                
                goto_name = f"GotoHome{seq}"
                mission_plan.add(goto_name, GotoLocalPosition(
                    waypoints=[list(target)],
                    yaws_deg=[yaw],
                    speed=[current_speed],
                    yaw_speed="sync"
                ))
                
                land_name = f"LandRTL{seq}"
                mission_plan.add(land_name, Land())
                current_enu = list(target)
                logger.info(f"[Seq {seq}] RTL: home=({target[0]:.1f}, {target[1]:.1f})")
                continue
            
            # Unknown command
            logger.warning(f"[Seq {seq}] Unsupported command {cmd}, skipped")
        
        return mission_plan.as_dict()


# =============================================================================
# DEPRECATED - Old Implementation (Keep for backwards compatibility)
# =============================================================================

# Validation thresholds (used by deprecated code)
MAX_REASONABLE_LOCAL_COORD = 50000.0
MAX_REASONABLE_GPS_OFFSET = 20000.0
MAX_REASONABLE_HOME_LOCAL = 100000.0


class CoordinateValidationError(Exception):
    """Raised when coordinate values are outside expected ranges."""
    pass


def validate_local_coordinate(value: float, name: str, context: str = "") -> None:
    """DEPRECATED: Validate that a local coordinate is within reasonable bounds."""
    if abs(value) > MAX_REASONABLE_LOCAL_COORD:
        msg = f"COORDINATE VALIDATION FAILED: {name} = {value:.2f}m is outside reasonable range"
        logger.error(msg)
        raise CoordinateValidationError(msg)


def validate_enu_position(enu: List[float], name: str, context: str = "") -> None:
    """DEPRECATED: Validate an ENU position [East, North, Up]."""
    labels = ["East", "North", "Up"]
    for i, (val, label) in enumerate(zip(enu, labels)):
        if i < 2 and abs(val) > MAX_REASONABLE_LOCAL_COORD:
            msg = f"COORDINATE VALIDATION FAILED: {name} {label} = {val:.2f}m is outside reasonable range"
            logger.error(msg)
            raise CoordinateValidationError(msg)


def validate_home_local_coords(x: float, y: float, z: float) -> None:
    """DEPRECATED: Validate HOME_POSITION local coordinates are reasonable."""
    if abs(x) > MAX_REASONABLE_HOME_LOCAL or abs(y) > MAX_REASONABLE_HOME_LOCAL:
        logger.warning(f"HOME_POSITION local coordinates appear to be global/UTM: x={x:.2f}, y={y:.2f}, z={z:.2f}")


def gps_to_enu_offset(lat: float, lon: float, ref_lat: float, ref_lon: float) -> List[float]:
    """DEPRECATED: Use gps_to_local_enu() instead."""
    east, north = gps_to_local_enu(lat, lon, ref_lat, ref_lon)
    return [east, north]


def ned_to_enu_deprecated(x_north: float, y_east: float, z_down: float) -> List[float]:
    """DEPRECATED: Use ned_to_enu() instead."""
    result = ned_to_enu((x_north, y_east, z_down))
    return list(result)


class PetalMissionTranslator:
    """Translates MAVLink waypoints to Petal mission plan."""

    @staticmethod
    def normalise_waypoint(
        seq: int,
        frame: int,
        command: int,
        current: int,
        autocontinue: int,
        param1: float,
        param2: float,
        param3: float,
        param4: float,
        x: Optional[int],
        y: Optional[int],
        z: float,
        home_lat_e7: int,
        home_lon_e7: int,
    ) -> Dict[str, Any]:
        """Normalise a MAVLink waypoint into a dictionary."""
        lat = (x / 1e7) if x is not None else None
        lon = (y / 1e7) if y is not None else None
        if abs(x or 0) < 10 and abs(y or 0) < 10:
            lat = None
            lon = None
        
        # Special handling for speed change commands (MAV_CMD_DO_CHANGE_SPEED = 178)
        MAV_CMD_DO_CHANGE_SPEED = getattr(mavutil.mavlink, "MAV_CMD_DO_CHANGE_SPEED", 178)
        if command == MAV_CMD_DO_CHANGE_SPEED:
            return {
                "seq": seq,
                "frame": frame,
                "command": command,
                "current": current,
                "autocontinue": autocontinue,
                "param1": float(param1),
                "param2": float(param2),
                "param3": float(param3),
                "param4": float(param4),
                "x": None,
                "y": None,
                "z": 0.0,
                "alt": 0.0,
                "lat": None,
                "lon": None,
                "speed_change": True,
            }
        
        MAV_CMD_NAV_TAKEOFF = getattr(mavutil.mavlink, "MAV_CMD_NAV_TAKEOFF", 22)
        MAV_CMD_NAV_LAND = getattr(mavutil.mavlink, "MAV_CMD_NAV_LAND", 21)

        if (x in (None, 0)) and (y in (None, 0)) and command in (MAV_CMD_NAV_TAKEOFF, MAV_CMD_NAV_LAND):
            lat = home_lat_e7 / 1e7
            lon = home_lon_e7 / 1e7
            x = home_lat_e7
            y = home_lon_e7
            
        if lat is not None and lon is not None:
            lat = float(lat)
            lon = float(lon)
            
        return {
            "seq": seq,
            "frame": frame,
            "command": command,
            "current": current,
            "autocontinue": autocontinue,
            "param1": float(param1),
            "param2": float(param2),
            "param3": float(param3),
            "param4": float(param4),
            "x": int(x) if x is not None else None,
            "y": int(y) if y is not None else None,
            "z": float(z),
            "alt": float(z),
            "lat": lat,
            "lon": lon,
        }

    def __init__(
        self, 
        home_lat: float, 
        home_lon: float, 
        home_local_x: float = 0.0,
        home_local_y: float = 0.0,
        home_local_z: float = 0.0,
        current_local_x: float = 0.0,
        current_local_y: float = 0.0,
        current_local_z: float = 0.0,
        gps_origin_lat: Optional[float] = None,
        gps_origin_lon: Optional[float] = None,
        gps_origin_alt: Optional[float] = None,
        use_mission_takeoff_location: bool = True,
    ):
        """Initialize mission translator.
        
        Args:
            home_lat: Home latitude (degrees)
            home_lon: Home longitude (degrees)
            home_local_x: Home position North (NED, from HOME_POSITION)
            home_local_y: Home position East (NED, from HOME_POSITION)
            home_local_z: Home position Down (NED, from HOME_POSITION)
            current_local_x: Current vehicle North position (NED, from LOCAL_POSITION_NED)
            current_local_y: Current vehicle East position (NED, from LOCAL_POSITION_NED)
            current_local_z: Current vehicle Down position (NED, from LOCAL_POSITION_NED)
            gps_origin_lat: GPS Global Origin latitude (degrees, from GPS_GLOBAL_ORIGIN)
            gps_origin_lon: GPS Global Origin longitude (degrees, from GPS_GLOBAL_ORIGIN)
            gps_origin_alt: GPS Global Origin altitude (meters, from GPS_GLOBAL_ORIGIN)
            use_mission_takeoff_location: Whether to fly to mission takeoff location after takeoff
        """
        self.home_lat = home_lat
        self.home_lon = home_lon
        self.gps_origin_lat = gps_origin_lat
        self.gps_origin_lon = gps_origin_lon
        self.gps_origin_alt = gps_origin_alt
        
        # Determine the reference point for coordinate conversion
        # Ideally, we use GPS_GLOBAL_ORIGIN. If not available, we fallback to Home.
        # GPS_GLOBAL_ORIGIN defaults to 0 if not received, so check for valid non-zero values
        if (self.gps_origin_lat is not None and self.gps_origin_lon is not None and 
            abs(self.gps_origin_lat) > 1e-6 and abs(self.gps_origin_lon) > 1e-6):
            self.ref_lat = self.gps_origin_lat
            self.ref_lon = self.gps_origin_lon
            self.ref_alt = self.gps_origin_alt or 0.0
            self.using_gps_origin = True
            logger.info(f"Using GPS_GLOBAL_ORIGIN as reference: ({self.ref_lat}, {self.ref_lon})")
        else:
            self.ref_lat = self.home_lat
            self.ref_lon = self.home_lon
            self.ref_alt = 0.0 # Relative to home
            self.using_gps_origin = False
            logger.warning("GPS_GLOBAL_ORIGIN not available. Falling back to HOME_POSITION as reference (0,0,0).")
        
        # Calculate Home ENU position relative to Reference
        if self.using_gps_origin:
            home_offset = gps_to_enu_offset(home_lat, home_lon, self.ref_lat, self.ref_lon)
            # Z = Home Alt - Origin Alt (approx) or just use 0 if we assume local Z=0 at origin
            # Actually, HOME_POSITION message gives us local x,y,z of home.
            # If we trust HOME_POSITION's local coordinates, we should use them directly?
            # User says: "If LOCAL_POSITION_NED says x=10, y=0, it means the drone is 10 meters North of the GPS_GLOBAL_ORIGIN."
            # So HOME_POSITION message should contain the local coordinates of Home relative to Origin.
            # Let's verify if calculated offset matches reported local coords.
            
            # Use reported local coords for Home if available, otherwise calculate
            # Convert NED to ENU
            reported_home_enu = ned_to_enu(home_local_x, home_local_y, home_local_z)
            
            # For now, let's trust the reported local coordinates for Home, as they define where Home is in the local frame.
            self.home_enu = reported_home_enu
            
            # Log comparison
            logger.info(f"Home ENU (Reported): {self.home_enu}")
            logger.info(f"Home ENU (Calculated from GPS): {home_offset} (ignoring Z)")
        else:
            # Fallback: Home is Origin (0,0,0)
            self.home_enu = [0.0, 0.0, 0.0]
            
        # Current vehicle position from LOCAL_POSITION_NED (NED -> ENU)
        self.current_enu = ned_to_enu(current_local_x, current_local_y, current_local_z)
        self.use_mission_takeoff_location = use_mission_takeoff_location
        
        # Log all coordinate info for debugging
        logger.info("=" * 60)
        logger.info("MissionTranslator Initialized")
        logger.info("=" * 60)
        logger.info(f"  Reference (Origin): Lat={self.ref_lat:.7f}, Lon={self.ref_lon:.7f} (Using GPS Origin: {self.using_gps_origin})")
        logger.info(f"  Home GPS: lat={home_lat:.7f}, lon={home_lon:.7f}")
        logger.info(f"  Home ENU: E={self.home_enu[0]:.2f}, N={self.home_enu[1]:.2f}, U={self.home_enu[2]:.2f}")
        logger.info(f"  Current ENU: E={self.current_enu[0]:.2f}, N={self.current_enu[1]:.2f}, U={self.current_enu[2]:.2f}")
        logger.info("=" * 60)
        
        # Validate converted coordinates
        try:
            validate_enu_position(self.home_enu, "Home ENU", "Check HOME_POSITION message x/y/z values")
            validate_enu_position(self.current_enu, "Current ENU", "Check LOCAL_POSITION_NED message x/y/z values")
        except CoordinateValidationError as e:
            logger.error(f"Coordinate validation failed during init: {e}")
            # Don't raise here - let translation continue but log the error
            # The validation in translate() will catch specific waypoint issues

    def translate(self, waypoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert MAVLink waypoints to Petal mission plan.
        
        All coordinates are converted to ENU (East-North-Up) frame for LeafSDK:
        - X = East
        - Y = North  
        - Z = Up (positive upward)
        
        The mission starts from the current vehicle position (from LOCAL_POSITION_NED),
        not from the home position. This ensures accurate positioning when the vehicle
        has moved from its original home location.
        """
        mission_data = {
            "edges": [],
            "id": "main",
            "nodes": []
        }
            
        previous_node_name = None
        current_speed = 0.5  # Default speed in m/s
        
        # Track current position in ENU frame [East, North, Up]
        # Start at CURRENT vehicle position (from LOCAL_POSITION_NED), not home
        current_enu = list(self.current_enu)
        
        MAV_CMD_DO_CHANGE_SPEED = getattr(mavutil.mavlink, "MAV_CMD_DO_CHANGE_SPEED", 178)
        MAV_CMD_NAV_TAKEOFF = getattr(mavutil.mavlink, "MAV_CMD_NAV_TAKEOFF", 22)
        MAV_CMD_NAV_LAND = getattr(mavutil.mavlink, "MAV_CMD_NAV_LAND", 21)
        MAV_CMD_NAV_RETURN_TO_LAUNCH = getattr(mavutil.mavlink, "MAV_CMD_NAV_RETURN_TO_LAUNCH", 20)
        MAV_CMD_NAV_WAYPOINT = getattr(mavutil.mavlink, "MAV_CMD_NAV_WAYPOINT", 16)

        for wp in waypoints:
            if not wp:
                continue
                
            command = wp.get("command")
            seq = wp["seq"]
            
            if command == MAV_CMD_DO_CHANGE_SPEED or wp.get("speed_change"):
                speed_ms = wp.get("param2", 0.5)
                if speed_ms > 0:
                    current_speed = float(speed_ms)
                    logger.info(f"Speed change at seq {seq}: {current_speed} m/s")
                continue
                
            if command == MAV_CMD_NAV_TAKEOFF:
                node_name = f"Takeoff{seq}"
                takeoff_alt = float(wp.get("alt", 5.0))
                
                # Get takeoff GPS coordinates
                lat = wp.get("lat")
                lon = wp.get("lon")
                
                # Create the Takeoff node
                node = {
                    "name": node_name,
                    "params": {
                        "alt": takeoff_alt
                    },
                    "type": "Takeoff"
                }
                mission_data["nodes"].append(node)
                
                # If configured to use mission takeoff location and coordinates are valid,
                # add a GotoRelative node to fly there after takeoff.
                if self.use_mission_takeoff_location:
                    if lat is not None and lon is not None and lat != 0 and lon != 0:
                        goto_node_name = f"GotoTakeoff{seq}"
                        # Get ENU offset from Reference GPS to target GPS
                        enu_offset = gps_to_enu_offset(lat, lon, self.ref_lat, self.ref_lon)
                        # Calculate absolute ENU position
                        # If using GPS Origin: WP_Local = Offset(Origin -> WP)
                        # If using Home Fallback: WP_Local = Offset(Home -> WP) (since Home is 0,0,0)
                        
                        abs_east = enu_offset[0]
                        abs_north = enu_offset[1]
                        
                        # Altitude handling:
                        # If using GPS Origin, we need to know absolute altitude or relative to origin.
                        # MAVLink alt is usually relative to Home or MSL.
                        # Here we assume 'takeoff_alt' is relative to Home.
                        # So Target Z = Home Z + Takeoff Alt
                        abs_up = self.home_enu[2] + takeoff_alt
                        
                        target_enu = [abs_east, abs_north, abs_up]
                        
                        # Validate waypoint coordinates
                        logger.info(f"GotoTakeoff{seq}: GPS({lat:.7f}, {lon:.7f}) -> ENU offset({enu_offset[0]:.2f}, {enu_offset[1]:.2f}) -> target({abs_east:.2f}, {abs_north:.2f}, {abs_up:.2f})")
                        validate_enu_position(target_enu, f"GotoTakeoff{seq}", f"GPS: lat={lat}, lon={lon}")
                        
                        # Calculate yaw towards takeoff location
                        # ENU yaw: atan2(North_delta, East_delta) gives 0°=East, 90°=North
                        delta_east = target_enu[0] - current_enu[0]
                        delta_north = target_enu[1] - current_enu[1]
                        
                        yaw_deg = math.degrees(math.atan2(delta_north, delta_east))
                        
                        # Update current position
                        current_enu = target_enu
                        
                        goto_node = {
                            "name": goto_node_name,
                            "params": {
                                "waypoints": [target_enu],  # Must be a list of waypoints
                                "yaws_deg": [yaw_deg],
                                "speed": [current_speed],
                                "yaw_speed": "sync"
                            },
                            "type": "GotoLocalPosition"
                        }
                        mission_data["nodes"].append(goto_node)
                        
                        mission_data["edges"].append({
                            "from": node_name,
                            "to": goto_node_name
                        })
                        
                        # Update previous node so next item links to the Goto node
                        previous_node_name = goto_node_name
                        continue # Skip standard previous_node_name update at bottom
                
                # If not using mission takeoff location, or takeoff is at home (0,0)
                # Update current position for subsequent waypoints
                # The current_enu is already updated by the GotoLocalPosition if use_mission_takeoff_location is True.
                # If it's False, the vehicle takes off at home position.
                # The Z component (Up) is updated below.
                
                # Takeoff updates Z position (Up in ENU)
                current_enu[2] = self.home_enu[2] + takeoff_alt
                    
            elif command == MAV_CMD_NAV_LAND:
                node_name = f"Land{seq}"
                lat = wp.get("lat")
                lon = wp.get("lon")
                alt = wp.get("alt")
                
                if lat is not None and lon is not None and lat != 0 and lon != 0:
                    # Get ENU offset from Reference GPS to target GPS
                    enu_offset = gps_to_enu_offset(lat, lon, self.ref_lat, self.ref_lon)
                    # For landing, altitude is typically the ground level or specified altitude
                    target_alt = float(alt) if alt else 0.0
                    
                    # Calculate absolute ENU position
                    abs_east = enu_offset[0]
                    abs_north = enu_offset[1]
                    # Target Z = Home Z + Target Alt (assuming relative to home)
                    abs_up = self.home_enu[2] + target_alt
                    
                    target_enu = [abs_east, abs_north, abs_up]
                    
                    # Validate waypoint coordinates
                    logger.info(f"Land{seq}: GPS({lat:.7f}, {lon:.7f}) -> ENU offset({enu_offset[0]:.2f}, {enu_offset[1]:.2f}) -> target({abs_east:.2f}, {abs_north:.2f}, {abs_up:.2f})")
                    validate_enu_position(target_enu, f"Land{seq}", f"GPS: lat={lat}, lon={lon}")
                    
                    # Calculate yaw towards landing location
                    delta_east = target_enu[0] - current_enu[0]
                    delta_north = target_enu[1] - current_enu[1]
                    
                    # ENU yaw: atan2(North_delta, East_delta) gives 0°=East, 90°=North
                    yaw_deg = math.degrees(math.atan2(delta_north, delta_east))
                    
                    # Update current position
                    current_enu = target_enu
                    
                    node = {
                        "name": node_name,
                        "params": {
                            "waypoints": [target_enu],  # Must be a list of waypoints
                            "yaws_deg": [yaw_deg],
                            "speed": [0.3],
                            "yaw_speed": "sync"
                        },
                        "type": "GotoLocalPosition"
                    }
                    mission_data["nodes"].append(node)
                    
                    land_node_name = f"LandAt{seq}"
                    land_node = {
                        "name": land_node_name,
                        "params": {},
                        "type": "Land"
                    }
                    mission_data["nodes"].append(land_node)
                    
                    if previous_node_name:
                        mission_data["edges"].append({
                            "from": previous_node_name,
                            "to": node_name
                        })
                    mission_data["edges"].append({
                        "from": node_name,
                        "to": land_node_name
                    })
                    previous_node_name = land_node_name
                    continue
                else:
                    node = {
                        "name": node_name,
                        "params": {},
                        "type": "Land"
                    }
                    mission_data["nodes"].append(node)
                    
            elif command == MAV_CMD_NAV_RETURN_TO_LAUNCH:
                # RTL is not directly supported in LeafSDK - convert to GotoLocalPosition + Land
                # Navigate to home position at current altitude, then land
                logger.info(f"Converting RTL at seq {seq} to GotoLocalPosition + Land")
                
                # First: go to home position at safe altitude (current altitude)
                goto_home_name = f"GotoHome{seq}"
                rtl_altitude = current_enu[2]  # Maintain current altitude for RTL (Up in ENU)
                home_target_enu = [self.home_enu[0], self.home_enu[1], rtl_altitude]
                
                # Validate RTL target coordinates
                logger.info(f"GotoHome{seq}: RTL to home_enu({self.home_enu[0]:.2f}, {self.home_enu[1]:.2f}) at alt {rtl_altitude:.2f}")
                validate_enu_position(home_target_enu, f"GotoHome{seq}", "RTL to home position")
                
                # Calculate yaw towards home (ENU: atan2(North, East) gives 0°=East, 90°=North)
                delta_east = home_target_enu[0] - current_enu[0]
                delta_north = home_target_enu[1] - current_enu[1]
                if abs(delta_east) > 0.1 or abs(delta_north) > 0.1:
                    yaw_to_home = math.degrees(math.atan2(delta_north, delta_east))
                else:
                    yaw_to_home = 0.0
                
                goto_home_node = {
                    "name": goto_home_name,
                    "params": {
                        "waypoints": [home_target_enu],  # Must be a list of waypoints
                        "yaws_deg": [yaw_to_home],
                        "speed": [current_speed],
                        "yaw_speed": "sync"
                    },
                    "type": "GotoLocalPosition"
                }
                mission_data["nodes"].append(goto_home_node)
                
                # Then: land at home
                land_name = f"LandRTL{seq}"
                land_node = {
                    "name": land_name,
                    "params": {},
                    "type": "Land"
                }
                mission_data["nodes"].append(land_node)
                
                # Add edges
                if previous_node_name:
                    mission_data["edges"].append({
                        "from": previous_node_name,
                        "to": goto_home_name
                    })
                mission_data["edges"].append({
                    "from": goto_home_name,
                    "to": land_name
                })
                
                # Update current position to home
                current_enu = home_target_enu
                previous_node_name = land_name
                continue
                    
            elif command == MAV_CMD_NAV_WAYPOINT:
                node_name = f"Waypoint{seq}"
                lat = wp.get("lat")
                lon = wp.get("lon")
                alt = wp.get("alt", 5.0)
                hold_time = float(wp.get("param1", 0.0))
                
                # Get explicit yaw from QGC plan (param4)
                explicit_yaw = wp.get("param4")
                
                if lat is not None and lon is not None:
                    # Get ENU offset from Reference GPS to target GPS
                    enu_offset = gps_to_enu_offset(lat, lon, self.ref_lat, self.ref_lon)
                    
                    # Calculate absolute ENU position
                    abs_east = enu_offset[0]
                    abs_north = enu_offset[1]
                    # Target Z = Home Z + Target Alt (assuming relative to home)
                    abs_up = self.home_enu[2] + float(alt)
                    
                    target_enu = [abs_east, abs_north, abs_up]
                    
                    # Validate waypoint coordinates
                    logger.info(f"Waypoint{seq}: GPS({lat:.7f}, {lon:.7f}) -> ENU offset({enu_offset[0]:.2f}, {enu_offset[1]:.2f}) -> target({abs_east:.2f}, {abs_north:.2f}, {abs_up:.2f})")
                    validate_enu_position(target_enu, f"Waypoint{seq}", f"GPS: lat={lat}, lon={lon}")
                    
                    # Determine yaw: use explicit if set, otherwise calculate towards waypoint
                    if explicit_yaw is not None and not (isinstance(explicit_yaw, float) and math.isnan(explicit_yaw)):
                        # User set explicit yaw in QGC
                        yaw = float(explicit_yaw)
                        logger.debug(f"Waypoint {seq}: Using explicit yaw {yaw}°")
                    else:
                        # Calculate yaw towards waypoint (from current position to target)
                        delta_east = target_enu[0] - current_enu[0]
                        delta_north = target_enu[1] - current_enu[1]
                        
                        if abs(delta_east) > 0.1 or abs(delta_north) > 0.1:
                            # ENU yaw: atan2(North_delta, East_delta) gives 0°=East, 90°=North
                            yaw = math.degrees(math.atan2(delta_north, delta_east))
                        else:
                            yaw = 0.0  # Default if no significant movement
                        logger.debug(f"Waypoint {seq}: Calculated yaw {yaw:.1f}° towards target")
                    
                    # Update current position AFTER yaw calculation
                    current_enu = target_enu
                    
                    node = {
                        "name": node_name,
                        "params": {
                            "waypoints": [target_enu],  # Must be a list of waypoints
                            "yaws_deg": [yaw],
                            "speed": [current_speed],
                            "yaw_speed": "sync"
                        },
                        "type": "GotoLocalPosition"
                    }
                    mission_data["nodes"].append(node)
                        
                    if hold_time > 0:
                        wait_node_name = f"Wait{seq}"
                        wait_node = {
                            "name": wait_node_name,
                            "params": {
                                "duration": float(hold_time)
                            },
                            "type": "Wait"
                        }
                        mission_data["nodes"].append(wait_node)
                            
                        if previous_node_name:
                            mission_data["edges"].append({
                                "from": previous_node_name,
                                "to": node_name
                            })
                        mission_data["edges"].append({
                            "from": node_name,
                            "to": wait_node_name
                        })
                        previous_node_name = wait_node_name
                        continue
                else:
                    logger.warning(f"Waypoint {seq} missing lat/lon, skipping")
                    continue
            else:
                logger.warning(f"Unsupported MAVLink command {command} at seq {seq}, skipping")
                continue
                
            if previous_node_name:
                mission_data["edges"].append({
                    "from": previous_node_name,
                    "to": node_name
                })
                
            previous_node_name = node_name
            
        return mission_data
