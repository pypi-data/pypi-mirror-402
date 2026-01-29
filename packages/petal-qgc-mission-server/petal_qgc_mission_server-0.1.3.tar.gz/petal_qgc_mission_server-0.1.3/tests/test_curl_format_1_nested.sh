#!/bin/bash
# Test Format 1: NESTED arrays [[lat,lon,alt]] - matches petal-leafsdk examples
echo "Testing Format 1: Nested waypoints [[lat,lon,alt]]"

curl -X 'POST' \
  'http://localhost:9000/petals/petal-mission-planner/mission/plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "id": "test_nested",
  "nodes": [
    {
      "name": "Takeoff",
      "type": "Takeoff",
      "params": {
        "alt": 1.0
      }
    },
    {
      "name": "Waypoint1",
      "type": "GotoGPSWaypoint",
      "params": {
        "waypoints": [[47.3977815, 8.5456798, 1.0]],
        "yaws_deg": [0.0],
        "speed": [0.5],
        "yaw_speed": [30.0]
      }
    },
    {
      "name": "Waypoint2",
      "type": "GotoGPSWaypoint",
      "params": {
        "waypoints": [[47.3977557, 8.545751, 1.0]],
        "yaws_deg": [0.0],
        "speed": [0.5],
        "yaw_speed": [30.0]
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
      "to": "Waypoint1"
    },
    {
      "from": "Waypoint1",
      "to": "Waypoint2"
    },
    {
      "from": "Waypoint2",
      "to": "Land"
    }
  ]
}'
