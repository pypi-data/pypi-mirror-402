#!/bin/bash
# Test curl command with corrected GotoGPSWaypoint format

curl -X 'POST' \
  'http://localhost:9000/petals/petal-mission-planner/mission/plan' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "edges": [
    {
      "from": "Takeoff0",
      "to": "Waypoint1"
    },
    {
      "from": "Waypoint1",
      "to": "Waypoint2"
    },
    {
      "from": "Waypoint2",
      "to": "Waypoint3"
    },
    {
      "from": "Waypoint3",
      "to": "Waypoint4"
    },
    {
      "from": "Waypoint4",
      "to": "RTL5"
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
        "waypoints": [[47.3977815, 8.5456798, 5.0]]
      },
      "type": "GotoGPSWaypoint"
    },
    {
      "name": "Waypoint2",
      "params": {
        "waypoints": [[47.3977557, 8.545751, 5.0]]
      },
      "type": "GotoGPSWaypoint"
    },
    {
      "name": "Waypoint3",
      "params": {
        "waypoints": [[47.3977157, 8.5456894, 5.0]]
      },
      "type": "GotoGPSWaypoint"
    },
    {
      "name": "Waypoint4",
      "params": {
        "waypoints": [[47.3977483, 8.5456279, 5.0]]
      },
      "type": "GotoGPSWaypoint"
    },
    {
      "name": "RTL5",
      "params": {},
      "type": "Land"
    }
  ]
}'
