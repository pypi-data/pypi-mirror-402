"""NEDPosition value object for local NED coordinates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NEDPosition:
    """Immutable local NED position (North-East-Down in meters).
    
    - north: Positive towards geographic north
    - east: Positive towards geographic east
    - down: Positive towards Earth center
    """
    north: float
    east: float
    down: float
    
    @classmethod
    def from_xyz(cls, x: float, y: float, z: float) -> NEDPosition:
        """Create from MAVLink x/y/z (already NED)."""
        return cls(north=x, east=y, down=z)
    
    @classmethod
    def zero(cls) -> NEDPosition:
        """Create a zero position."""
        return cls(0.0, 0.0, 0.0)
    
    @property
    def altitude_agl(self) -> float:
        """Altitude above ground (inverted down)."""
        return -self.down
    
    @property
    def x(self) -> float:
        """Alias for north."""
        return self.north
    
    @property
    def y(self) -> float:
        """Alias for east."""
        return self.east
    
    @property
    def z(self) -> float:
        """Alias for down."""
        return self.down
    
    def __str__(self) -> str:
        return f"NED({self.north:.2f}, {self.east:.2f}, {self.down:.2f})"
