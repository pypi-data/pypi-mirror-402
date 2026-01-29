from petal_qgc_mission_server.mission_translator import PetalMissionTranslator
import math

def test_mission_logic():
    print("Testing Mission Logic (Absolute Positioning with GPS Origin)...")
    
    # Mock GPS Origin (0,0,0 Local NED)
    origin_lat = 47.397700
    origin_lon = 8.545500
    origin_alt = 480.0
    
    # Mock Home Location (slightly offset from origin)
    # Let's say Home is 10m North, 10m East of Origin
    # 1 deg lat ~ 111320m
    # 10m lat ~ 10/111320 deg
    lat_offset = 10.0 / 111320.0
    lon_offset = 10.0 / (111320.0 * math.cos(math.radians(origin_lat)))
    
    home_lat = origin_lat + lat_offset
    home_lon = origin_lon + lon_offset
    home_alt = 488.0 # 8m above origin
    
    # Local Home Coordinates (NED) relative to Origin
    # Should be x=10 (North), y=10 (East), z=-8 (Up is negative Down)
    home_local_x = 10.0
    home_local_y = 10.0
    home_local_z = -8.0
    
    # Sample mission: Takeoff -> Waypoint (Origin) -> RTL
    waypoints = [
        {
            "seq": 0,
            "command": 22, # TAKEOFF
            "alt": 10.0,
            "lat": home_lat, 
            "lon": home_lon,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0
        },
        {
            "seq": 1,
            "command": 16, # WAYPOINT
            "alt": 20.0,
            "lat": origin_lat, # Go to Origin
            "lon": origin_lon,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0
        },
        {
            "seq": 2,
            "command": 20, # RTL
            "alt": 0,
            "lat": 0,
            "lon": 0,
            "param1": 0, "param2": 0, "param3": 0, "param4": 0
        }
    ]
    
    translator = PetalMissionTranslator(
        home_lat=home_lat, 
        home_lon=home_lon,
        home_local_x=home_local_x,
        home_local_y=home_local_y,
        home_local_z=home_local_z,
        current_local_x=home_local_x,
        current_local_y=home_local_y,
        current_local_z=home_local_z,
        gps_origin_lat=origin_lat,
        gps_origin_lon=origin_lon,
        gps_origin_alt=origin_alt,
        use_mission_takeoff_location=True
    )
    mission = translator.translate(waypoints)
    
    nodes = mission["nodes"]
    
    # Verify Waypoint at Origin
    # Should be close to (0,0) in ENU (East=0, North=0)
    # Altitude: Origin Alt is 480. Waypoint Alt is 20 (relative to home? or MSL?)
    # MAVLink waypoint alt frame depends on frame. Assuming relative to home usually.
    # If relative to home (488), target alt = 488 + 20 = 508.
    # Origin is 480. So Up from Origin = 508 - 480 = 28.
    # Or: Home is at Z=-8 (8m Up). Target is 20m above Home. So 28m Up from Origin.
    
    wp_node = next((n for n in nodes if n['name'] == 'Waypoint1'), None)
    if wp_node:
        target = wp_node['params']['waypoints'][0]
        print(f"Waypoint Node Found (Target Origin):")
        print(f" - Target ENU: {target}")
        
        if abs(target[0]) < 1.0 and abs(target[1]) < 1.0:
            print("✅ Waypoint correctly targets Origin (0,0) in ENU")
        else:
            print(f"❌ Waypoint target mismatch. Expected (0,0), got ({target[0]:.2f}, {target[1]:.2f})")
            
    else:
        print("❌ Waypoint Node not found")

if __name__ == "__main__":
    test_mission_logic()
