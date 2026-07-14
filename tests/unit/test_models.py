"""Tests for part profile data models."""

import pytest

from solidworks_mcp.parts.models import (
    BoundingBox,
    CatalogEntry,
    CategorySummary,
    ConnectionPoint,
    Geometry,
    HolePattern,
    MateSuggestion,
    MountingFace,
    PartProfile,
    profile_from_dict,
)


class TestBoundingBox:
    def test_frozen(self):
        bbox = BoundingBox(x=48, y=48, z=288)
        with pytest.raises(AttributeError):
            bbox.x = 100

    def test_defaults(self):
        bbox = BoundingBox(x=1, y=2, z=3)
        assert bbox.unit == "mm"


class TestPartProfile:
    def test_frozen(self):
        profile = PartProfile(
            sku="1120-0001-0288",
            name="U-Channel",
            category="structure/channel",
            source_file="channel/1120-0001-0288.step",
            geometry=Geometry(bounding_box=BoundingBox(x=48, y=48, z=288)),
        )
        with pytest.raises(AttributeError):
            profile.name = "Modified"


class TestProfileFromDict:
    def test_basic_deserialization(self):
        data = {
            "sku": "1120-0001-0288",
            "name": "U-Channel 288mm",
            "category": "structure/channel",
            "source_file": "channel/1120-0001-0288.step",
            "geometry": {
                "bounding_box": {"x": 48, "y": 48, "z": 288, "unit": "mm"},
                "volume_cm3": 42.5,
                "mass_grams": 115,
            },
            "compatible_with": ["gobilda_8mm_pattern"],
            "tags": ["channel"],
        }

        profile = profile_from_dict(data)

        assert profile.sku == "1120-0001-0288"
        assert profile.geometry.bounding_box.z == 288
        assert profile.geometry.mass_grams == 115
        assert "gobilda_8mm_pattern" in profile.compatible_with
        assert "channel" in profile.tags

    def test_with_hole_patterns(self):
        data = {
            "sku": "test",
            "name": "Test",
            "category": "test",
            "source_file": "test.step",
            "geometry": {"bounding_box": {"x": 1, "y": 1, "z": 1}},
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
        }

        profile = profile_from_dict(data)

        assert len(profile.hole_patterns) == 1
        hp = profile.hole_patterns[0]
        assert hp.pitch_x_mm == 8
        assert hp.bolt_size == "M4"
        assert hp.count == 216

    def test_with_connection_points(self):
        data = {
            "sku": "test",
            "name": "Test",
            "category": "test",
            "source_file": "test.step",
            "geometry": {"bounding_box": {"x": 1, "y": 1, "z": 1}},
            "connection_points": [
                {
                    "type": "shaft_bore",
                    "diameter_mm": 8,
                    "profile": "D_bore",
                    "compatible_with": ["REX_8mm_shaft"],
                    "location": [24, 24, 0],
                },
            ],
        }

        profile = profile_from_dict(data)

        assert len(profile.connection_points) == 1
        cp = profile.connection_points[0]
        assert cp.connection_type == "shaft_bore"
        assert cp.diameter_mm == 8
        assert "REX_8mm_shaft" in cp.compatible_with

    def test_missing_optional_fields(self):
        data = {
            "sku": "minimal",
            "name": "Minimal Part",
            "category": "test",
            "source_file": "test.step",
            "geometry": {"bounding_box": {"x": 1, "y": 1, "z": 1}},
        }

        profile = profile_from_dict(data)

        assert profile.mounting_faces == ()
        assert profile.hole_patterns == ()
        assert profile.connection_points == ()
        assert profile.compatible_with == ()
        assert profile.tags == ()


class TestCatalogEntry:
    def test_frozen(self):
        entry = CatalogEntry(sku="test", name="Test", category="test")
        with pytest.raises(AttributeError):
            entry.name = "Modified"


class TestMateSuggestion:
    def test_creation(self):
        suggestion = MateSuggestion(
            mate_type="coincident",
            a_ref="face_top",
            b_ref="face_bottom",
            confidence=0.9,
        )
        assert suggestion.mate_type == "coincident"
        assert suggestion.confidence == 0.9
