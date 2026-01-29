"""Mission storage and persistence."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from .. import logger
from .models import Waypoint


class MissionStorage:
    """Manages waypoint collection with efficient Dict-based storage.
    
    Replaces the inefficient List[Optional[Dict]] approach with:
    - Dict[int, Waypoint] for O(1) access by sequence number
    - Type-safe Waypoint objects
    - Clear API for waypoint management
    """
    
    def __init__(self):
        """Initialize mission storage."""
        self._waypoints: Dict[int, Waypoint] = {}
        self._mission_type: int = 0
    
    def add_waypoint(self, wp: Waypoint) -> None:
        """Add or update a waypoint.
        
        Args:
            wp: The waypoint to add
        """
        self._waypoints[wp.seq] = wp
    
    def get_waypoint(self, seq: int) -> Optional[Waypoint]:
        """Get a waypoint by sequence number.
        
        Args:
            seq: The sequence number
            
        Returns:
            The waypoint, or None if not found
        """
        return self._waypoints.get(seq)
    
    def get_all_waypoints(self) -> List[Waypoint]:
        """Get all waypoints sorted by sequence number.
        
        Returns:
            List of waypoints in sequence order
        """
        return [self._waypoints[seq] for seq in sorted(self._waypoints.keys())]
    
    def get_waypoints_as_dicts(self) -> List[dict]:
        """Get all waypoints as dictionaries (for backwards compatibility).
        
        Returns:
            List of waypoint dictionaries in sequence order
        """
        return [wp.to_dict() for wp in self.get_all_waypoints()]
    
    def total(self) -> int:
        """Get total number of waypoints.
        
        Returns:
            Number of waypoints
        """
        return len(self._waypoints)
    
    def clear(self) -> None:
        """Clear all waypoints."""
        self._waypoints.clear()
    
    def set_mission_type(self, mission_type: int) -> None:
        """Set the mission type.
        
        Args:
            mission_type: The mission type (MAV_MISSION_TYPE_*)
        """
        self._mission_type = mission_type
    
    def get_mission_type(self) -> int:
        """Get the mission type.
        
        Returns:
            The mission type
        """
        return self._mission_type
    
    def save_to_file(self, path: Path) -> None:
        """Save mission to QGC WPL format file.
        
        Args:
            path: Path to save the mission file
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            lines = self._to_wpl_lines()
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            logger.info(f"Saved mission to {path} ({self.total()} waypoints)")
        except Exception as exc:
            logger.error(f"Failed to save mission to {path}: {exc}")
            raise
    
    def load_from_file(self, path: Path) -> int:
        """Load mission from QGC WPL format file.
        
        Args:
            path: Path to the mission file
            
        Returns:
            Number of waypoints loaded
        """
        try:
            content = path.read_text(encoding="utf-8")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            
            if not lines or not lines[0].startswith("QGC WPL"):
                logger.warning(f"Invalid mission file format: {path}")
                return 0
            
            self.clear()
            
            # Parse waypoints (skip header line)
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) < 12:
                    logger.warning(f"Skipping invalid waypoint line: {line}")
                    continue
                
                try:
                    wp = Waypoint(
                        seq=int(parts[0]),
                        current=int(parts[1]),
                        frame=int(parts[2]),
                        command=int(parts[3]),
                        param1=float(parts[4]),
                        param2=float(parts[5]),
                        param3=float(parts[6]),
                        param4=float(parts[7]),
                        x=int(float(parts[8]) * 1e7) if float(parts[8]) != 0 else None,
                        y=int(float(parts[9]) * 1e7) if float(parts[9]) != 0 else None,
                        z=float(parts[10]),
                        autocontinue=int(parts[11]),
                        lat=float(parts[8]) if float(parts[8]) != 0 else None,
                        lon=float(parts[9]) if float(parts[9]) != 0 else None,
                        alt=float(parts[10]),
                    )
                    self.add_waypoint(wp)
                except (ValueError, IndexError) as exc:
                    logger.warning(f"Failed to parse waypoint line: {line} - {exc}")
                    continue
            
            logger.info(f"Loaded {self.total()} waypoints from {path}")
            return self.total()
            
        except Exception as exc:
            logger.error(f"Failed to load mission from {path}: {exc}")
            raise
    
    def _to_wpl_lines(self) -> List[str]:
        """Convert waypoints to QGC WPL format lines.
        
        Returns:
            List of WPL format lines
        """
        def fmt(value: float) -> str:
            """Format float value for WPL file."""
            if math.isnan(value):
                return "0.000000"
            return f"{value:.6f}"
        
        lines = ["QGC WPL 110"]
        
        for wp in self.get_all_waypoints():
            # Convert x/y back to lat/lon degrees
            lat = wp.lat if wp.lat is not None else (wp.x / 1e7 if wp.x is not None else 0.0)
            lon = wp.lon if wp.lon is not None else (wp.y / 1e7 if wp.y is not None else 0.0)
            
            line = "\t".join([
                str(wp.seq),
                str(wp.current),
                str(wp.frame),
                str(wp.command),
                fmt(wp.param1),
                fmt(wp.param2),
                fmt(wp.param3),
                fmt(wp.param4),
                fmt(lat),
                fmt(lon),
                fmt(wp.z),
                str(wp.autocontinue),
            ])
            lines.append(line)
        
        return lines
    
    def to_json(self) -> str:
        """Export mission as JSON.
        
        Returns:
            JSON string representation
        """
        data = {
            "waypoints": self.get_waypoints_as_dicts(),
            "count": self.total(),
            "mission_type": self._mission_type,
        }
        return json.dumps(data, indent=2)
    
    def from_json(self, json_str: str) -> int:
        """Import mission from JSON.
        
        Args:
            json_str: JSON string representation
            
        Returns:
            Number of waypoints loaded
        """
        try:
            data = json.loads(json_str)
            self.clear()
            
            for wp_dict in data.get("waypoints", []):
                wp = Waypoint.from_dict(wp_dict)
                self.add_waypoint(wp)
            
            self._mission_type = data.get("mission_type", 0)
            
            logger.info(f"Loaded {self.total()} waypoints from JSON")
            return self.total()
            
        except Exception as exc:
            logger.error(f"Failed to load mission from JSON: {exc}")
            raise
