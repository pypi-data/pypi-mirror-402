import json

from petal_qgc_mission_server.mission_adapter import MissionAdapter, QGC_MISSION_CMD_CHANNEL


class DummyRedisProxy:
    def __init__(self):
        self.calls = []

    def publish(self, channel, message):
        self.calls.append((channel, message))
        return 1


def test_publish_mission_plan_to_redis_serializes_payload():
    adapter = MissionAdapter.__new__(MissionAdapter)
    adapter.redis_proxy = DummyRedisProxy()

    mission_payload = {
        "id": "main",
        "nodes": [{"name": "Takeoff0", "type": "Takeoff", "params": {"alt": 5.0}}],
        "edges": [],
    }

    adapter._publish_mission_plan_to_redis(mission_payload)

    assert len(adapter.redis_proxy.calls) == 1
    channel, message = adapter.redis_proxy.calls[0]
    assert channel == QGC_MISSION_CMD_CHANNEL

    decoded = json.loads(message)
    assert decoded["command"] == "mission.plan"
    assert decoded["payload"] == mission_payload
    assert decoded["source"] == "petal-qgc-mission-server"
    assert "message_id" in decoded and decoded["message_id"].startswith("mission-plan-")
