"""
Main plugin module for px4-simulator-petal
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import __version__, logger
from .mavlink_server import QGCMavlinkServer
from petal_app_manager.plugins.base import Petal
from petal_app_manager.plugins.decorators import http_action
from petal_app_manager.proxies.external import MavLinkExternalProxy
from petal_app_manager.proxies.redis import RedisProxy


class PetalQGCMissionServer(Petal):
    # logging that class is being loaded
    logger.info("Loading PetalQGCMissionServer plugin")

    """
    Main petal class for PetalQGCMissionServer.
    
    QGC Mission Adapter petal that provides connectivity between QGC and LeafSDK.
    """

    name = "petal-qgc-mission-server"
    version = __version__

    def __init__(self, *_: Any, **__: Any):
        logger.info("Initializing PetalQGCMissionServer plugin")
        super().__init__()
        self._mavlink_server: Optional[QGCMavlinkServer] = None
        self._pending_mission: Optional[Path] = None
        self._lock = asyncio.Lock()
        self._status_message = "Petal initialized successfully"
        self._startup_time = None

    def startup(self) -> None:
        """Called when the petal is started."""
        super().startup()
        self._startup_time = datetime.now()
        self._status_message = f"Petal started at {self._startup_time.isoformat()}"
        logger.info(f"{self.name} petal started successfully")
        asyncio.create_task(self.start())

    def shutdown(self) -> None:
        """Called when the petal is stopped."""
        super().shutdown()
        self._status_message = "Petal is shutting down"
        if self._mavlink_server is not None and self._mavlink_server.is_running:
            asyncio.create_task(self.stop())
        logger.info(f"{self.name} petal shut down")

    def get_required_proxies(self) -> List[str]:
        """
        Return a list of proxy names that this petal requires.
        
        This adapter petal requires the external MAVLink proxy.
        """
        return ["ext_mavlink", "redis"]

    def get_optional_proxies(self) -> List[str]:
        """
        Return a list of proxy names that this petal can optionally use.
        
        This adapter petal currently does not use optional proxies.
        """
        return []

    def get_petal_status(self) -> Dict[str, Any]:
        """
        Return custom status information for this petal.
        """
        status = {
            "message": self._status_message,
            "startup_time": self._startup_time.isoformat() if self._startup_time else None,
            "uptime_seconds": (datetime.now() - self._startup_time).total_seconds() if self._startup_time else 0,
            "simulator_running": self._mavlink_server is not None and self._mavlink_server.is_running if self._mavlink_server else False,
        }
        return status

    def _ensure_server(self) -> QGCMavlinkServer:
        if self._mavlink_server is None:
            mavlink_proxy: MavLinkExternalProxy = self._proxies["ext_mavlink"]
            redis_proxy: RedisProxy = self._proxies["redis"]
            self._mavlink_server = QGCMavlinkServer(mavlink_proxy, redis_proxy)
            if self._pending_mission:
                try:
                    self._mavlink_server.load_mission(self._pending_mission)
                except FileNotFoundError:
                    logger.warning("Pending mission %s missing", self._pending_mission)
                finally:
                    self._pending_mission = None
        return self._mavlink_server

    @http_action(
        method="GET",
        path="/health",
        description="Health check endpoint for this petal"
    )
    async def health_check(self):
        """
        Health check endpoint that reports proxy requirements and petal status.
        """
        logger.info("Health check endpoint called")
        health_info = {
            "petal_name": self.name,
            "petal_version": self.version,
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "required_proxies": self.get_required_proxies(),
            "optional_proxies": self.get_optional_proxies(),
            "petal_status": self.get_petal_status()
        }
        return health_info

    @http_action(
        method="POST",
        path="/start",
        description="Start the MAVLink server loop"
    )
    async def start(self) -> None:
        async with self._lock:
            server = self._ensure_server()
            if server.is_running:
                logger.info("Server already running")
                return
            await server.start()
        return {"status": "started"}

    @http_action(
        method="POST",
        path="/stop",
        description="Stop the MAVLink server loop"
    )
    async def stop(self) -> None:
        async with self._lock:
            server = self._mavlink_server
            if server is None:
                logger.info("Server not running")
                return
            if not server.is_running:
                logger.info("Server not running")
                return
            await server.stop()
            server.close()
            self._mavlink_server = None
        return {"status": "stopped"}

    @http_action(
        method="GET",
        path="/status",
        description="Return the current adapter status"
    )
    async def status(self) -> Dict[str, Any]:
        async with self._lock:
            if self._mavlink_server is None:
                return {
                    "connection": "external_proxy",
                    "armed": False,
                    "mission_state": "IDLE",
                    "mode": "STANDBY",
                    "system_status": 0,
                    "position": None,
                }
            return self._mavlink_server.status()

    @http_action(
        method="POST",
        path="/load-mission",
        description="Load a QGC mission file into the adapter"
    )
    async def load_mission(self, mission_path: str) -> Dict[str, Any]:
        path = Path(mission_path)
        async with self._lock:
            if self._mavlink_server is None:
                self._pending_mission = path
                return {"loaded": 0, "mission": str(path), "pending": True}
            count = self._mavlink_server.load_mission(path)
            return {"loaded": count, "mission": str(path), "pending": False}
