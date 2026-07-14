"""
SolidWorks MCP Package
----------------------
Model Context Protocol server for SolidWorks automation.

The automation layer (COM/pywin32) is only available on Windows.
All other subpackages (tools, mcp, parts, utils) work cross-platform.

Version: 4.0.0
Author: Samsaam Ali Baig, Sateesh Seetharamaiah
"""

__version__ = "4.0.0"
__author__ = "Samsaam Ali Baig, Sateesh Seetharamaiah"

from .config import get_config, reload_config, save_config, SolidWorksConfig
from .constants import SwErrors, SwPlanes, SwDocumentTypes, SwViews

# Automation layer requires pywin32 (Windows only).
# Guard the import so cross-platform code (parts server, tests on Linux) works.
try:
    from .automation import SolidWorksAutomation
    from .utils import (
        UnitConverter,
        mm, cm, inch, ft,
        find_solidworks,
        find_template,
        get_solidworks_info,
    )
    _HAS_AUTOMATION = True
except ImportError:
    SolidWorksAutomation = None  # type: ignore[assignment,misc]
    _HAS_AUTOMATION = False

__all__ = [
    # Version
    "__version__",
    "__author__",

    # Config (cross-platform)
    "get_config",
    "reload_config",
    "save_config",
    "SolidWorksConfig",

    # Constants (cross-platform)
    "SwErrors",
    "SwPlanes",
    "SwDocumentTypes",
    "SwViews",

    # Automation (Windows only)
    "SolidWorksAutomation",
    "_HAS_AUTOMATION",
]
