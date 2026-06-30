"""API publica del nucleo de analisis de SimGhostInputs."""

from . import wear
from .compare import compare, corner_coaching, delta_trace
from .corners import detect_corners, extract_milestones, samples
from .lap import Lap
from .normalize import resample

__all__ = [
    "Lap",
    "samples",
    "detect_corners",
    "extract_milestones",
    "compare",
    "corner_coaching",
    "delta_trace",
    "resample",
    "wear",
]
