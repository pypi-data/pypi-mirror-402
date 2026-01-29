#!/bin/bash
# Test Format 2: FLAT arrays [lat, lon, alt] - current implementation
echo "Testing Format 2: Flat waypoints [lat, lon, alt]"

curl -X POST \
  'http://localhost:9000/petals/petal-mission-planner/mission/plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "id": "main",
    "nodes": [
      {
        "name": "Takeoff",
        "type": "Takeoff",
        "params": { "alt": 1.0 }
      },
      {
        "name": "GotoLocalWaypoint 1",
        "type": "GotoLocalPosition",
        "params": {
          "speed": [0.2],
          "waypoints": [
            [0.5, 6, 1]
          ],
          "yaw_speed": [30],
          "yaws_deg": [0]
        }
      },
      {
        "name": "Wait 1",
        "type": "Wait",
        "params": { "duration": 2 }
      },
      {
        "name": "GotoGPSWaypoint 1",
        "type": "GotoGPSWaypoint",
        "params": {
          "waypoints": [[47.3977815, 8.5456798, 1.0]],
          "yaws_deg": [0.0],
          "speed": [0.5],
          "yaw_speed": [30.0]
        }
      },
      {
        "name": "GotoGPSWaypoint 2",
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
        "to": "Wait 1"
      },
      {
        "from": "Wait 1",
        "to": "GotoLocalWaypoint 1"
      },
      {
        "from": "GotoLocalWaypoint 1",
        "to": "GotoGPSWaypoint 1"
      },
      {
        "from": "GotoGPSWaypoint 1",
        "to": "GotoGPSWaypoint 2"
      },
      {
        "from": "GotoGPSWaypoint 2",
        "to": "Land"
      }
    ]
  }'
