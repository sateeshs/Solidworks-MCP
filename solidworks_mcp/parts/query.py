"""Tiered search engine for goBILDA part profiles.

Tier 1: Category index (loaded at startup, ~2KB)
Tier 2: Catalog entries per category (loaded on demand, ~3KB each)
Tier 3: Full profiles per part (loaded on demand, ~1-2KB each)

All data is read from the profiles/ directory as JSON files.
"""

import json
import logging
import os
from dataclasses import asdict
from typing import Any

from .models import (
    CatalogEntry,
    CategorySummary,
    MateSuggestion,
    PartProfile,
    profile_from_dict,
)

logger = logging.getLogger(__name__)


class PartsQuery:
    """Tiered search engine over goBILDA part profiles."""

    def __init__(self, profiles_dir: str) -> None:
        self._profiles_dir = profiles_dir
        self._categories: list[CategorySummary] = []
        self._catalog: dict[str, CatalogEntry] = {}  # sku -> entry
        self._profiles_cache: dict[str, PartProfile] = {}  # sku -> profile
        self._loaded = False

    def load(self) -> None:
        """Load tier 1 (categories) and tier 2 (catalog) at startup."""
        categories_path = os.path.join(self._profiles_dir, "categories.json")
        catalog_path = os.path.join(self._profiles_dir, "catalog.json")

        if os.path.isfile(categories_path):
            with open(categories_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._categories = [
                CategorySummary(
                    category=c.get("category", ""),
                    count=c.get("count", 0),
                    description=c.get("description", ""),
                )
                for c in data
            ]
            logger.info("Loaded %d categories", len(self._categories))

        if os.path.isfile(catalog_path):
            with open(catalog_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for entry in data:
                sku = entry.get("sku", "")
                self._catalog[sku] = CatalogEntry(
                    sku=sku,
                    name=entry.get("name", ""),
                    category=entry.get("category", ""),
                    bbox_x=entry.get("bbox_x", 0),
                    bbox_y=entry.get("bbox_y", 0),
                    bbox_z=entry.get("bbox_z", 0),
                    mass_grams=entry.get("mass_grams", 0),
                    hole_count=entry.get("hole_count", 0),
                    bolt_size=entry.get("bolt_size", ""),
                    tags=tuple(entry.get("tags", [])),
                )
            logger.info("Loaded %d catalog entries", len(self._catalog))

        self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def part_count(self) -> int:
        return len(self._catalog)

    def list_categories(self) -> list[dict[str, Any]]:
        """Return tier 1 category summaries."""
        return [
            {"category": c.category, "count": c.count, "description": c.description}
            for c in self._categories
        ]

    def search_parts(
        self,
        query: str,
        category: str | None = None,
        min_length: float | None = None,
        max_length: float | None = None,
        bolt_size: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search catalog entries by keyword, with optional filters."""
        query_lower = query.lower()
        results = []

        for entry in self._catalog.values():
            # Category filter
            if category and not entry.category.startswith(category):
                continue

            # Keyword match on name, sku, category, tags
            searchable = f"{entry.name} {entry.sku} {entry.category} {' '.join(entry.tags)}"
            if query_lower not in searchable.lower():
                continue

            # Dimension filters (use longest dimension)
            max_dim = max(entry.bbox_x, entry.bbox_y, entry.bbox_z)
            if min_length is not None and max_dim < min_length:
                continue
            if max_length is not None and max_dim > max_length:
                continue

            # Bolt size filter
            if bolt_size and entry.bolt_size != bolt_size:
                continue

            results.append({
                "sku": entry.sku,
                "name": entry.name,
                "category": entry.category,
                "bbox": {"x": entry.bbox_x, "y": entry.bbox_y, "z": entry.bbox_z},
                "mass_grams": entry.mass_grams,
                "hole_count": entry.hole_count,
                "bolt_size": entry.bolt_size,
            })

            if len(results) >= limit:
                break

        return results

    def get_part_profile(self, sku: str) -> dict[str, Any] | None:
        """Load and return a full tier 3 profile for a part."""
        # Check cache
        if sku in self._profiles_cache:
            return self._profile_to_dict(self._profiles_cache[sku])

        # Find the profile file
        catalog_entry = self._catalog.get(sku)
        if not catalog_entry:
            return None

        # Try category-based path: profiles/gobilda/channel/1120-0001-0288.json
        category_dir = catalog_entry.category.split("/")[-1]
        profile_path = os.path.join(
            self._profiles_dir, category_dir, f"{sku}.json"
        )

        if not os.path.isfile(profile_path):
            # Fallback: flat directory
            profile_path = os.path.join(self._profiles_dir, f"{sku}.json")

        if not os.path.isfile(profile_path):
            logger.warning("Profile not found for SKU %s at %s", sku, profile_path)
            return None

        with open(profile_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        profile = profile_from_dict(data)
        self._profiles_cache[sku] = profile
        return self._profile_to_dict(profile)

    def find_compatible_parts(
        self,
        tag: str,
        category: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find parts compatible with a given tag (e.g., 'REX_8mm_shaft')."""
        tag_lower = tag.lower()
        results = []

        for entry in self._catalog.values():
            if category and not entry.category.startswith(category):
                continue

            if any(tag_lower in t.lower() for t in entry.tags):
                results.append({
                    "sku": entry.sku,
                    "name": entry.name,
                    "category": entry.category,
                })
                if len(results) >= limit:
                    break

        return results

    def suggest_mates(
        self, sku_a: str, sku_b: str
    ) -> list[dict[str, Any]]:
        """Suggest mate constraints between two parts based on their profiles."""
        profile_a = self.get_part_profile(sku_a)
        profile_b = self.get_part_profile(sku_b)

        if not profile_a or not profile_b:
            return []

        suggestions: list[dict[str, Any]] = []

        # Match hole patterns with same bolt size
        for hp_a in profile_a.get("hole_patterns", []):
            for hp_b in profile_b.get("hole_patterns", []):
                if hp_a.get("bolt_size") == hp_b.get("bolt_size"):
                    if hp_a.get("pitch_x_mm") == hp_b.get("pitch_x_mm"):
                        suggestions.append({
                            "type": "coincident",
                            "a_ref": hp_a.get("face_ref", ""),
                            "b_ref": hp_b.get("face_ref", ""),
                            "confidence": 0.9,
                            "reason": f"Matching {hp_a.get('bolt_size')} hole pattern "
                                      f"at {hp_a.get('pitch_x_mm')}mm pitch",
                        })

        # Match shaft bores
        for cp_a in profile_a.get("connection_points", []):
            for cp_b in profile_b.get("connection_points", []):
                a_compat = set(cp_a.get("compatible_with", []))
                b_compat = set(cp_b.get("compatible_with", []))
                if a_compat & b_compat:
                    shared = a_compat & b_compat
                    suggestions.append({
                        "type": "concentric",
                        "a_ref": cp_a.get("face_ref", ""),
                        "b_ref": cp_b.get("face_ref", ""),
                        "confidence": 0.85,
                        "reason": f"Compatible via {', '.join(shared)}",
                    })

        return suggestions

    @staticmethod
    def _profile_to_dict(profile: PartProfile) -> dict[str, Any]:
        """Convert a PartProfile to a JSON-serializable dict."""
        return {
            "sku": profile.sku,
            "name": profile.name,
            "category": profile.category,
            "source_file": profile.source_file,
            "geometry": {
                "bounding_box": {
                    "x": profile.geometry.bounding_box.x,
                    "y": profile.geometry.bounding_box.y,
                    "z": profile.geometry.bounding_box.z,
                    "unit": profile.geometry.bounding_box.unit,
                },
                "volume_cm3": profile.geometry.volume_cm3,
                "mass_grams": profile.geometry.mass_grams,
                "center_of_mass": list(profile.geometry.center_of_mass),
            },
            "mounting_faces": [
                {
                    "id": f.id,
                    "normal": list(f.normal),
                    "area_mm2": f.area_mm2,
                    "center": list(f.center),
                    "type": f.face_type,
                    "has_holes": f.has_holes,
                    "hole_pattern_ref": f.hole_pattern_ref,
                }
                for f in profile.mounting_faces
            ],
            "hole_patterns": [
                {
                    "id": hp.id,
                    "face_ref": hp.face_ref,
                    "hole_diameter_mm": hp.hole_diameter_mm,
                    "hole_type": hp.hole_type,
                    "pitch_x_mm": hp.pitch_x_mm,
                    "pitch_y_mm": hp.pitch_y_mm,
                    "grid": list(hp.grid),
                    "bolt_size": hp.bolt_size,
                    "count": hp.count,
                }
                for hp in profile.hole_patterns
            ],
            "connection_points": [
                {
                    "type": cp.connection_type,
                    "compatible_with": list(cp.compatible_with),
                    "face_ref": cp.face_ref,
                    "pattern_ref": cp.pattern_ref,
                    "diameter_mm": cp.diameter_mm,
                    "profile": cp.profile,
                    "location": list(cp.location),
                }
                for cp in profile.connection_points
            ],
            "compatible_with": list(profile.compatible_with),
            "can_mate_with": list(profile.can_mate_with),
            "tags": list(profile.tags),
        }
