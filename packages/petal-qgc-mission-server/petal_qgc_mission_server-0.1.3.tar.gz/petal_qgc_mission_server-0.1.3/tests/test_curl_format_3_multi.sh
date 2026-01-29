#!/bin/bash
# Test Format 3: Multiple waypoints in single node - matches GotoLocalWaypoint 2 example
echo "Testing Format 3: Multiple waypoints in single node [[lat1,lon1,alt1], [lat2,lon2,alt2]]"

curl -X 'POST' \
  'http://localhost:9000/petals/petal-mission-planner/mission/plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "test_multi",
  "nodes": [
    {
      "name": "Takeoff",
      "type": "Takeoff",
      "params": {
        "alt": 1.0
      }
    },
    {
      "name": "WaypointMulti",
      "type": "GotoGPSWaypoint",
      "params": {
        "waypoints": [
          [47.3977815, 8.5456798, 1.0],
          [47.3977557, 8.545751, 1.0]
        ],
        "yaws_deg": [0.0, 0.0],
        "speed": [0.5, 0.5],
        "yaw_speed": [30.0, 30.0]
      }
    },
    {
      "name": "Land",
      "type": "Land",
      "params": {}
    }
  ],
  "edges": [
    {
      "from": "Takeoff",
      "to": "WaypointMulti"
    },
    {
      "from": "WaypointMulti",
      "to": "Land"
    }
  ]
}'
