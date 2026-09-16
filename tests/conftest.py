"""Shared pytest fixtures for Solidworks-MCP tests.

Provides mock COM fixtures for Windows-only code and
sample profile data for Parts Intelligence testing.
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock

# Stub Windows-only modules so solidworks_mcp.automation can be imported on Linux.
for _mod in ("win32com", "win32com.client", "win32com.client.dynamic", "pythoncom",
             "win32gui", "win32ui", "win32con"):
    sys.modules.setdefault(_mod, MagicMock())

import pytest


# --- Sample goBILDA profile data ---

SAMPLE_CHANNEL_PROFILE = {
    "sku": "1120-0001-0288",
    "name": "U-Channel 288mm",
    "category": "structure/channel",
    "source_file": "channel/1120-0001-0288.step",
    "geometry": {
        "bounding_box": {"x": 48, "y": 48, "z": 288, "unit": "mm"},
        "volume_cm3": 42.5,
        "mass_grams": 115,
        "center_of_mass": [24, 24, 144],
    },
    "mounting_faces": [
        {
            "id": "face_top",
            "normal": [0, 1, 0],
            "area_mm2": 13824,
            "center": [24, 48, 144],
            "type": "planar",
            "has_holes": True,
            "hole_pattern_ref": "pattern_0",
        },
    ],
    "hole_patterns": [
        {
            "id": "pattern_0",
            "face_ref": "face_top",
            "hole_diameter_mm": 4.2,
            "hole_type": "through",
            "pitch_x_mm": 8,
            "pitch_y_mm": 8,
            "grid": [6, 36],
            "bolt_size": "M4",
            "count": 216,
        },
    ],
    "connection_points": [
        {
            "type": "bolt_hole_grid",
            "compatible_with": ["M4_bolt", "gobilda_8mm_pattern"],
            "face_ref": "face_top",
            "pattern_ref": "pattern_0",
        },
        {
            "type": "shaft_bore",
            "diameter_mm": 8,
            "profile": "D_bore",
            "compatible_with": ["REX_8mm_shaft"],
            "location": [24, 24, 0],
        },
    ],
    "compatible_with": ["gobilda_8mm_pattern", "M4_socket_head", "REX_8mm_shaft"],
    "can_mate_with": ["brackets", "plates", "motors", "servos"],
    "tags": ["channel", "structure", "gobilda_8mm_pattern", "REX_8mm_shaft"],
}

SAMPLE_BRACKET_PROFILE = {
    "sku": "1141-0001-0001",
    "name": "90 Degree Bracket",
    "category": "structure/bracket",
    "source_file": "brackets/1141-0001-0001.step",
    "geometry": {
        "bounding_box": {"x": 48, "y": 48, "z": 48, "unit": "mm"},
        "volume_cm3": 8.2,
        "mass_grams": 22,
        "center_of_mass": [24, 24, 24],
    },
    "mounting_faces": [
        {
            "id": "face_a",
            "normal": [0, 1, 0],
            "area_mm2": 2304,
            "center": [24, 48, 24],
            "type": "planar",
            "has_holes": True,
            "hole_pattern_ref": "pattern_0",
        },
    ],
    "hole_patterns": [
        {
            "id": "pattern_0",
            "face_ref": "face_a",
            "hole_diameter_mm": 4.2,
            "hole_type": "through",
            "pitch_x_mm": 8,
            "pitch_y_mm": 8,
            "grid": [6, 6],
            "bolt_size": "M4",
            "count": 36,
        },
    ],
    "connection_points": [
        {
            "type": "bolt_hole_grid",
            "compatible_with": ["M4_bolt", "gobilda_8mm_pattern"],
            "face_ref": "face_a",
            "pattern_ref": "pattern_0",
        },
    ],
    "compatible_with": ["gobilda_8mm_pattern", "M4_socket_head"],
    "can_mate_with": ["channel", "plates"],
    "tags": ["bracket", "structure", "gobilda_8mm_pattern"],
}

SAMPLE_WHEEL_PROFILE = {
    "sku": "2900-0005-0002",
    "name": "96mm Mecanum Wheel (Right)",
    "category": "motion/wheel",
    "source_file": "wheels/2900-0005-0002.step",
    "geometry": {
        "bounding_box": {"x": 96, "y": 96, "z": 50, "unit": "mm"},
        "volume_cm3": 120.5,
        "mass_grams": 180,
        "center_of_mass": [48, 48, 25],
    },
    "mounting_faces": [],
    "hole_patterns": [],
    "connection_points": [
        {
            "type": "shaft_bore",
            "diameter_mm": 8,
            "profile": "D_bore",
            "compatible_with": ["REX_8mm_shaft"],
            "location": [48, 48, 25],
        },
    ],
    "compatible_with": ["REX_8mm_shaft"],
    "can_mate_with": ["shafts", "hubs"],
    "tags": ["mecanum", "wheel", "motion", "REX_8mm_shaft"],
}

SAMPLE_CATEGORIES = [
    {"category": "structure/channel", "count": 35, "description": "U-channels and C-channels"},
    {"category": "structure/bracket", "count": 28, "description": "90-degree and angle brackets"},
    {"category": "motion/wheel", "count": 15, "description": "Mecanum, omni, and traction wheels"},
    {"category": "motion/motor", "count": 18, "description": "Yellow Jacket and other motors"},
    {"category": "motion/shaft", "count": 30, "description": "REX 8mm shafts"},
]

SAMPLE_CATALOG = [
    {
        "sku": "1120-0001-0288",
        "name": "U-Channel 288mm",
        "category": "structure/channel",
        "bbox_x": 48, "bbox_y": 48, "bbox_z": 288,
        "mass_grams": 115,
        "hole_count": 216,
        "bolt_size": "M4",
        "tags": ["channel", "structure", "gobilda_8mm_pattern", "REX_8mm_shaft"],
    },
    {
        "sku": "1141-0001-0001",
        "name": "90 Degree Bracket",
        "category": "structure/bracket",
        "bbox_x": 48, "bbox_y": 48, "bbox_z": 48,
        "mass_grams": 22,
        "hole_count": 36,
        "bolt_size": "M4",
        "tags": ["bracket", "structure", "gobilda_8mm_pattern"],
    },
    {
        "sku": "2900-0005-0002",
        "name": "96mm Mecanum Wheel (Right)",
        "category": "motion/wheel",
        "bbox_x": 96, "bbox_y": 96, "bbox_z": 50,
        "mass_grams": 180,
        "hole_count": 0,
        "bolt_size": "",
        "tags": ["mecanum", "wheel", "motion", "REX_8mm_shaft"],
    },
]


@pytest.fixture
def profiles_dir(tmp_path):
    """Create a temporary profiles directory with sample data."""
    # Write categories
    categories_path = tmp_path / "categories.json"
    categories_path.write_text(json.dumps(SAMPLE_CATEGORIES))

    # Write catalog
    catalog_path = tmp_path / "catalog.json"
    catalog_path.write_text(json.dumps(SAMPLE_CATALOG))

    # Write individual profiles
    channel_dir = tmp_path / "channel"
    channel_dir.mkdir()
    (channel_dir / "1120-0001-0288.json").write_text(
        json.dumps(SAMPLE_CHANNEL_PROFILE)
    )

    bracket_dir = tmp_path / "bracket"
    bracket_dir.mkdir()
    (bracket_dir / "1141-0001-0001.json").write_text(
        json.dumps(SAMPLE_BRACKET_PROFILE)
    )

    wheel_dir = tmp_path / "wheel"
    wheel_dir.mkdir()
    (wheel_dir / "2900-0005-0002.json").write_text(
        json.dumps(SAMPLE_WHEEL_PROFILE)
    )

    return str(tmp_path)
