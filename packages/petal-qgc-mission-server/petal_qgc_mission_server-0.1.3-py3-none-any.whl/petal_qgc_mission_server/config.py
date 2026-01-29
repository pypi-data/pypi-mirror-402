"""Paths to mission resource artifacts."""

from pathlib import Path


RESOURCE_DIR = Path(__file__).resolve().parent / "resources"
CURRENT_MISSION_PATH = RESOURCE_DIR / "current_mission.waypoints"

