#!/bin/bash
# Auto-generated curl script for testing mission upload
# Mission ID: main
# Nodes: 4
# Edges: 3

curl -X POST http://localhost:6379/publish \
  -H "Content-Type: application/json" \
  -d '{"message_id": "mission-plan-debug", "command": "mission.plan", "payload": {"id": "main", "nodes": [{"name": "Takeoff0", "type": "Takeoff", "params": {"alt": 2.0}}, {"name": "GotoStart0", "type": "GotoLocalPosition", "params": {"waypoints": [[0.0036860808902661846, -0.001147748349410449, 2.13950352370739]], "yaws_deg": [-56.97756872852811], "speed": [0.5], "yaw_speed": "sync"}}, {"name": "Waypoint1", "type": "GotoLocalPosition", "params": {"waypoints": [[75.69582454358994, 60.72391225099295, 2.13950352370739]], "yaws_deg": [38.73880888740083], "speed": [0.5], "yaw_speed": "sync"}}, {"name": "Waypoint2", "type": "GotoLocalPosition", "params": {"waypoints": [[-39.217576308201494, 53.33226425162081, 2.13950352370739]], "yaws_deg": [-176.31959735643426], "speed": [0.5], "yaw_speed": "sync"}}], "edges": [{"from": "Takeoff0", "to": "GotoStart0", "condition": null}, {"from": "GotoStart0", "to": "Waypoint1", "condition": null}, {"from": "Waypoint1", "to": "Waypoint2", "condition": null}]}, "source": "petal-qgc-mission-server"}'
