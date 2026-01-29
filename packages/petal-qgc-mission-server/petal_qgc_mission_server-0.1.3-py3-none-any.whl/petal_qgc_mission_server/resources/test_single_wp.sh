#!/bin/bash
# Test with single waypoint (not nested in array)
curl -X 'POST' \
  'http://localhost:9000/petals/petal-mission-planner/mission/plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "edges": [
    {
      "from": "Takeoff0",
      "to": "Waypoint1"
    }
  ],
  "id": "main",
  "nodes": [
    {
      "name": "Takeoff0",
      "params": {
        "alt": 5.0
      },
      "type": "Takeoff"
    },
    {
      "name": "Waypoint1",
      "params": {
        "waypoints": [47.3977815, 8.5456798, 5.0]
      },
      "type": "GotoGPSWaypoint"
    }
  ]
}'
