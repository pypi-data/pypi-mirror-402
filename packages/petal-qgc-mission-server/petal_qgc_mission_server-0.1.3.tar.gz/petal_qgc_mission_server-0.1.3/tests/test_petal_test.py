"""
Tests for px4-simulator-petal
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from petal_test.plugin import PetalTest


class TestPetalTest:
    """Test suite for the px4-simulator-petal petal."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.petal = PetalTest()
        
    def test_petal_initialization(self):
        """Test that the petal initializes correctly."""
        assert self.petal.name == "px4-simulator-petal"
        assert self.petal.version == "0.1.0"
        assert self.petal._status_message == "Petal initialized successfully"
        
    def test_required_proxies(self):
        """Test that required proxies are correctly specified."""
        required = self.petal.get_required_proxies()
        assert isinstance(required, list)
        # Add specific assertions based on your petal's requirements
        
    def test_optional_proxies(self):
        """Test that optional proxies are correctly specified."""
        optional = self.petal.get_optional_proxies()
        assert isinstance(optional, list)
        
    def test_petal_status(self):
        """Test that petal status is correctly returned."""
        status = self.petal.get_petal_status()
        assert isinstance(status, dict)
        assert "message" in status
        assert "startup_time" in status
        assert "uptime_seconds" in status
        
    @pytest.mark.asyncio
    async def test_hello_world_endpoint(self):
        """Test the hello world endpoint."""
        response = await self.petal.hello_world()
        assert isinstance(response, dict)
        assert "message" in response
        assert "petal_name" in response
        assert "petal_version" in response
        assert "timestamp" in response
        assert response["petal_name"] == "px4-simulator-petal"
        assert response["petal_version"] == "0.1.0"
        
    @pytest.mark.asyncio
    async def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        # Mock proxies
        mock_proxies = {}
        self.petal._proxies = mock_proxies
        
        response = await self.petal.health_check()
        assert isinstance(response, dict)
        assert "petal_name" in response
        assert "petal_version" in response
        assert "status" in response
        assert "required_proxies" in response
        assert "optional_proxies" in response
        assert "petal_status" in response
        
    # Add more tests for your custom endpoints and functionality
