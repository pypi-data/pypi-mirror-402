"""QGC Mission Adapter packaged for the Petal ecosystem."""

from __future__ import annotations

import logging
from importlib.metadata import PackageNotFoundError, version as _pkg_version

logger = logging.getLogger(__name__)
logger.info("[petal-qgc-mission-server]: Loading QGCMissionAdapterPetal plugin")

try:
    __version__ = _pkg_version("petal-qgc-mission-server")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__", "logger"]
