"""
SolidWorks Automation Package
-----------------------------
Complete automation class combining all operations.
"""

from .base import SolidWorksAutomation as _BaseAutomation
from .documents import DocumentOperations
from .sketches import SketchOperations
from .features import FeatureOperations
from .assemblies import AssemblyOperations
from .patterns import PatternOperations


class SolidWorksAutomation(_BaseAutomation, DocumentOperations,
                           SketchOperations, FeatureOperations,
                           AssemblyOperations, PatternOperations):
    """
    Complete SolidWorks automation class

    Combines all operation mixins:
    - Base: Connection, document access, utilities
    - Documents: Create, open, save, close documents
    - Sketches: Create sketches, draw 2D geometry
    - Features: Extrude, cut, fillet, chamfer
    - Assemblies: Insert components, add mates, inspect tree
    - Patterns: Linear and circular component patterns
    """
    pass


__all__ = [
    "SolidWorksAutomation",
    "DocumentOperations",
    "SketchOperations",
    "FeatureOperations",
    "AssemblyOperations",
    "PatternOperations",
]
