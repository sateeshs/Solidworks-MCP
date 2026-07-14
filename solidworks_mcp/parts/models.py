"""Data models for part profiles, catalog entries, and search results.

All models are frozen dataclasses for immutability.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoundingBox:
    """Bounding box dimensions in mm."""
    x: float
    y: float
    z: float
    unit: str = "mm"


@dataclass(frozen=True)
class Geometry:
    """Part geometry summary."""
    bounding_box: BoundingBox
    volume_cm3: float = 0.0
    mass_grams: float = 0.0
    center_of_mass: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class MountingFace:
    """A planar face suitable for mounting."""
    id: str
    normal: tuple[float, float, float]
    area_mm2: float
    center: tuple[float, float, float]
    face_type: str = "planar"
    has_holes: bool = False
    hole_pattern_ref: str = ""


@dataclass(frozen=True)
class HolePattern:
    """A regular pattern of holes on a face."""
    id: str
    face_ref: str
    hole_diameter_mm: float
    hole_type: str  # "through", "blind", "countersink"
    pitch_x_mm: float
    pitch_y_mm: float
    grid: tuple[int, int]
    bolt_size: str  # "M4", "M3", etc.
    count: int


@dataclass(frozen=True)
class ConnectionPoint:
    """A connection interface on a part."""
    connection_type: str  # "bolt_hole_grid", "shaft_bore", "motor_mount_pattern"
    compatible_with: tuple[str, ...] = ()
    face_ref: str = ""
    pattern_ref: str = ""
    diameter_mm: float = 0.0
    profile: str = ""
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class PartProfile:
    """Complete semantic profile of a goBILDA part."""
    sku: str
    name: str
    category: str
    source_file: str
    geometry: Geometry
    mounting_faces: tuple[MountingFace, ...] = ()
    hole_patterns: tuple[HolePattern, ...] = ()
    connection_points: tuple[ConnectionPoint, ...] = ()
    compatible_with: tuple[str, ...] = ()
    can_mate_with: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CatalogEntry:
    """Lightweight entry in the searchable catalog (tier 2)."""
    sku: str
    name: str
    category: str
    bbox_x: float = 0.0
    bbox_y: float = 0.0
    bbox_z: float = 0.0
    mass_grams: float = 0.0
    hole_count: int = 0
    bolt_size: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategorySummary:
    """Summary of a part category (tier 1)."""
    category: str
    count: int
    description: str = ""


@dataclass(frozen=True)
class MateSuggestion:
    """A suggested mate between two parts."""
    mate_type: str  # "coincident", "concentric", "distance"
    a_ref: str
    b_ref: str
    value: float = 0.0  # For distance/angle mates
    confidence: float = 1.0


def profile_from_dict(data: dict[str, Any]) -> PartProfile:
    """Deserialize a profile JSON dict into a PartProfile."""
    geo_data = data.get("geometry", {})
    bbox_data = geo_data.get("bounding_box", {})

    geometry = Geometry(
        bounding_box=BoundingBox(
            x=bbox_data.get("x", 0),
            y=bbox_data.get("y", 0),
            z=bbox_data.get("z", 0),
            unit=bbox_data.get("unit", "mm"),
        ),
        volume_cm3=geo_data.get("volume_cm3", 0),
        mass_grams=geo_data.get("mass_grams", 0),
        center_of_mass=tuple(geo_data.get("center_of_mass", [0, 0, 0])),
    )

    mounting_faces = tuple(
        MountingFace(
            id=f.get("id", ""),
            normal=tuple(f.get("normal", [0, 0, 0])),
            area_mm2=f.get("area_mm2", 0),
            center=tuple(f.get("center", [0, 0, 0])),
            face_type=f.get("type", "planar"),
            has_holes=f.get("has_holes", False),
            hole_pattern_ref=f.get("hole_pattern_ref", ""),
        )
        for f in data.get("mounting_faces", [])
    )

    hole_patterns = tuple(
        HolePattern(
            id=hp.get("id", ""),
            face_ref=hp.get("face_ref", ""),
            hole_diameter_mm=hp.get("hole_diameter_mm", 0),
            hole_type=hp.get("hole_type", "through"),
            pitch_x_mm=hp.get("pitch_x_mm", 0),
            pitch_y_mm=hp.get("pitch_y_mm", 0),
            grid=tuple(hp.get("grid", [0, 0])),
            bolt_size=hp.get("bolt_size", ""),
            count=hp.get("count", 0),
        )
        for hp in data.get("hole_patterns", [])
    )

    connection_points = tuple(
        ConnectionPoint(
            connection_type=cp.get("type", ""),
            compatible_with=tuple(cp.get("compatible_with", [])),
            face_ref=cp.get("face_ref", ""),
            pattern_ref=cp.get("pattern_ref", ""),
            diameter_mm=cp.get("diameter_mm", 0),
            profile=cp.get("profile", ""),
            location=tuple(cp.get("location", [0, 0, 0])),
        )
        for cp in data.get("connection_points", [])
    )

    return PartProfile(
        sku=data.get("sku", ""),
        name=data.get("name", ""),
        category=data.get("category", ""),
        source_file=data.get("source_file", ""),
        geometry=geometry,
        mounting_faces=mounting_faces,
        hole_patterns=hole_patterns,
        connection_points=connection_points,
        compatible_with=tuple(data.get("compatible_with", [])),
        can_mate_with=tuple(data.get("can_mate_with", [])),
        tags=tuple(data.get("tags", [])),
    )
