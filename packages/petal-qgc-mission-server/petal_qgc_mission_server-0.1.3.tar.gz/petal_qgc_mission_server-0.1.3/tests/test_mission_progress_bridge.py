"""Tests for MissionProgressBridge in mavlink_server.py."""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from petal_qgc_mission_server.mavlink_server import MissionProgressBridge
from petal_qgc_mission_server.adapter_state import AdapterState
from petal_qgc_mission_server.mission_handler import MissionProtocolHandler


class TestMissionProgressBridge:
    """Test suite for MissionProgressBridge class."""
    
    @pytest.fixture
    def mock_redis_proxy(self):
        """Create a mock Redis proxy."""
        return Mock()
    
    @pytest.fixture
    def adapter_state(self):
        """Create an adapter state instance."""
        return AdapterState()
    
    @pytest.fixture
    def mock_mission_handler(self):
        """Create a mock mission handler with waypoint mapping."""
        handler = Mock(spec=MissionProtocolHandler)
        handler.waypoints = [
            {"seq": 0, "command": 22},  # Takeoff
            {"seq": 1, "command": 16},  # Waypoint1
            {"seq": 2, "command": 16},  # Waypoint2
            {"seq": 3, "command": 21},  # Land
        ]
        handler.step_to_waypoint_map = {
            "Takeoff0": 0,
            "Waypoint1": 1,
            "Waypoint2": 2,
            "Land3": 3,
        }
        handler.waypoint_to_step_map = {
            0: "Takeoff0",
            1: "Waypoint1",
            2: "Waypoint2",
            3: "Land3",
        }
        return handler
    
    @pytest.fixture
    def mock_conn(self):
        """Create a mock MAVLink connection."""
        conn = Mock()
        conn.mav = Mock()
        conn.mav.mission_item_reached_send = Mock()
        return conn
    
    @pytest.fixture
    def mock_send_statustext(self):
        """Create a mock statustext sender."""
        return Mock()
    
    @pytest.fixture
    def bridge(self, mock_redis_proxy, adapter_state, mock_mission_handler, mock_conn, mock_send_statustext):
        """Create a MissionProgressBridge instance."""
        return MissionProgressBridge(
            redis_proxy=mock_redis_proxy,
            adapter_state=adapter_state,
            mission_handler=mock_mission_handler,
            conn=mock_conn,
            send_statustext_fn=mock_send_statustext,
        )
    
    def test_is_last_step_with_last_waypoint(self, bridge):
        """Test _is_last_step returns True for the last waypoint."""
        assert bridge._is_last_step("Land3") is True
    
    def test_is_last_step_with_middle_waypoint(self, bridge):
        """Test _is_last_step returns False for middle waypoints."""
        assert bridge._is_last_step("Waypoint1") is False
        assert bridge._is_last_step("Waypoint2") is False
    
    def test_is_last_step_with_first_waypoint(self, bridge):
        """Test _is_last_step returns False for the first waypoint."""
        assert bridge._is_last_step("Takeoff0") is False
    
    def test_is_last_step_with_unknown_step(self, bridge):
        """Test _is_last_step returns False for unknown step IDs."""
        assert bridge._is_last_step("UnknownStep") is False
    
    def test_is_last_step_with_none(self, bridge):
        """Test _is_last_step returns False for None."""
        assert bridge._is_last_step(None) is False
    
    def test_is_last_step_with_empty_waypoints(self, bridge, mock_mission_handler):
        """Test _is_last_step returns False when no waypoints exist."""
        mock_mission_handler.waypoints = []
        assert bridge._is_last_step("Land3") is False
    
    def test_handle_progress_message_mission_complete(self, bridge, mock_conn):
        """Test that mission completion triggers MISSION_ITEM_REACHED for last waypoint."""
        progress_data = json.dumps({
            "mission_id": "test_mission_123",
            "status": {
                "state": "COMPLETED",
                "step_id": "Land3",
                "step_completed": True,
            }
        })
        
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", progress_data)
        
        # Should send MISSION_ITEM_REACHED for seq 3 (last waypoint)
        mock_conn.mav.mission_item_reached_send.assert_called_once_with(3)
    
    def test_handle_progress_message_last_step_completed(self, bridge, mock_conn):
        """Test that completing the last step triggers mission completion logic."""
        progress_data = json.dumps({
            "mission_id": "test_mission_456",
            "status": {
                "state": "RUNNING",
                "step_id": "Land3",
                "step_completed": True,
            }
        })
        
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", progress_data)
        
        # Should detect last step and send MISSION_ITEM_REACHED
        mock_conn.mav.mission_item_reached_send.assert_called_once_with(3)
    
    def test_handle_progress_message_middle_step_no_completion(self, bridge, mock_conn):
        """Test that completing a middle step doesn't trigger mission completion."""
        progress_data = json.dumps({
            "mission_id": "test_mission_789",
            "status": {
                "state": "RUNNING",
                "step_id": "Waypoint1",
                "step_completed": True,
            }
        })
        
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", progress_data)
        
        # Should NOT send MISSION_ITEM_REACHED (not the last step)
        mock_conn.mav.mission_item_reached_send.assert_not_called()
    
    def test_handle_progress_message_invalid_json(self, bridge, mock_conn):
        """Test that invalid JSON is handled gracefully."""
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", "invalid{json")
        
        # Should not crash and not send any messages
        mock_conn.mav.mission_item_reached_send.assert_not_called()
    
    def test_handle_progress_message_mission_start(self, bridge, mock_send_statustext):
        """Test that mission start sends a status text message."""
        progress_data = json.dumps({
            "mission_id": "test_mission_start",
            "status": {
                "state": "RUNNING",
                "step_id": "Takeoff0",
                "step_completed": False,
            }
        })
        
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", progress_data)
        
        # Should send mission started status text
        mock_send_statustext.assert_called_once()
        args = mock_send_statustext.call_args[0]
        assert "Mission started" in args[0]
        assert "test_mission_start" in args[0]
    
    def test_handle_progress_message_with_missing_step(self, bridge, mock_conn):
        """Test handling progress message when step_id is missing."""
        progress_data = json.dumps({
            "mission_id": "test_mission_no_step",
            "status": {
                "state": "RUNNING",
                "step_completed": True,
            }
        })
        
        # Should not crash even without a step_id
        bridge._handle_progress_message("/petal/qgc_mission_adapter/progress", progress_data)
        
        # Should not send MISSION_ITEM_REACHED
        mock_conn.mav.mission_item_reached_send.assert_not_called()
    
    def test_setup_listeners_subscribes_to_channels(self, bridge, mock_redis_proxy):
        """Test that setup_listeners subscribes to the correct Redis channels."""
        bridge.setup_listeners()
        
        # Should subscribe to both progress and leg channels
        assert mock_redis_proxy.subscribe.call_count == 2
        
        # Get the channel names from the calls
        calls = mock_redis_proxy.subscribe.call_args_list
        channels = [call[0][0] for call in calls]
        
        assert "/petal/qgc_mission_adapter/progress" in channels
        assert "/petal/qgc_mission_adapter/mission_leg" in channels
    
    def test_setup_listeners_with_no_redis(self, adapter_state, mock_mission_handler, mock_conn, mock_send_statustext):
        """Test that setup_listeners handles missing Redis gracefully."""
        bridge = MissionProgressBridge(
            redis_proxy=None,
            adapter_state=adapter_state,
            mission_handler=mock_mission_handler,
            conn=mock_conn,
            send_statustext_fn=mock_send_statustext,
        )
        
        # Should not crash when Redis is unavailable
        bridge.setup_listeners()
