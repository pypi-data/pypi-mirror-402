"""Altitude value object with reference frame."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AltitudeReference(Enum):
    """Altitude reference frame."""
    MSL = "msl"
    AGL = "agl"
    RELATIVE = "relative"


@dataclass(frozen=True)
class Altitude:
    """Altitude with explicit reference frame."""
    value_m: float
    reference: AltitudeReference
    
    @classmethod
    def msl(cls, meters: float) -> Altitude:
        return cls(meters, AltitudeReference.MSL)
    
    @classmethod
    def relative(cls, meters: float) -> Altitude:
        return cls(meters, AltitudeReference.RELATIVE)
    
    def to_msl(self, home_alt_m: float) -> float:
        """Convert to MSL altitude value."""
        if self.reference == AltitudeReference.MSL:
            return self.value_m
        elif self.reference == AltitudeReference.RELATIVE:
            return self.value_m + home_alt_m
        return self.value_m + home_alt_m  # Default assumption
    
    def to_relative(self, home_alt_m: float) -> float:
        """Convert to relative altitude value."""
        if self.reference == AltitudeReference.RELATIVE:
            return self.value_m
        elif self.reference == AltitudeReference.MSL:
            return self.value_m - home_alt_m
        return self.value_m
    
    def __str__(self) -> str:
        return f"{self.value_m:.1f}m {self.reference.value.upper()}"
