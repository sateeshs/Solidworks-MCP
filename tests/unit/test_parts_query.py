"""Tests for the Parts Intelligence query engine."""

import pytest

from solidworks_mcp.parts.query import PartsQuery


class TestPartsQueryLoad:
    def test_load_from_valid_directory(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        assert engine.is_loaded
        assert engine.part_count == 3

    def test_load_from_missing_directory(self, tmp_path):
        engine = PartsQuery(str(tmp_path / "nonexistent"))
        engine.load()

        assert engine.is_loaded
        assert engine.part_count == 0

    def test_not_loaded_by_default(self, profiles_dir):
        engine = PartsQuery(profiles_dir)

        assert not engine.is_loaded


class TestListCategories:
    def test_returns_all_categories(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        categories = engine.list_categories()

        assert len(categories) == 5
        assert categories[0]["category"] == "structure/channel"
        assert categories[0]["count"] == 35

    def test_empty_when_not_loaded(self, tmp_path):
        engine = PartsQuery(str(tmp_path / "empty"))
        engine.load()

        assert engine.list_categories() == []


class TestSearchParts:
    def test_search_by_keyword(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("channel")

        assert len(results) == 1
        assert results[0]["sku"] == "1120-0001-0288"
        assert results[0]["name"] == "U-Channel 288mm"

    def test_search_by_sku(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("2900-0005")

        assert len(results) == 1
        assert results[0]["sku"] == "2900-0005-0002"

    def test_search_mecanum(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("mecanum")

        assert len(results) == 1
        assert "Mecanum" in results[0]["name"]

    def test_search_with_category_filter(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("", category="structure")

        assert len(results) == 2
        assert all(r["category"].startswith("structure") for r in results)

    def test_search_with_min_length(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("", category="structure", min_length=100)

        assert len(results) == 1
        assert results[0]["sku"] == "1120-0001-0288"

    def test_search_with_bolt_size(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("", bolt_size="M4")

        assert len(results) == 2  # channel and bracket have M4

    def test_search_no_results(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("nonexistent_part_xyz")

        assert results == []

    def test_search_with_limit(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.search_parts("", limit=1)

        assert len(results) == 1


class TestGetPartProfile:
    def test_get_existing_profile(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        profile = engine.get_part_profile("1120-0001-0288")

        assert profile is not None
        assert profile["sku"] == "1120-0001-0288"
        assert profile["name"] == "U-Channel 288mm"
        assert profile["geometry"]["bounding_box"]["z"] == 288
        assert len(profile["hole_patterns"]) == 1
        assert profile["hole_patterns"][0]["bolt_size"] == "M4"
        assert profile["hole_patterns"][0]["pitch_x_mm"] == 8

    def test_get_missing_profile(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        profile = engine.get_part_profile("9999-9999-9999")

        assert profile is None

    def test_profile_caching(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        # Load same profile twice
        profile1 = engine.get_part_profile("1120-0001-0288")
        profile2 = engine.get_part_profile("1120-0001-0288")

        assert profile1 == profile2


class TestFindCompatibleParts:
    def test_find_by_shaft_tag(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.find_compatible_parts("REX_8mm_shaft")

        assert len(results) == 2  # channel and wheel
        skus = {r["sku"] for r in results}
        assert "1120-0001-0288" in skus
        assert "2900-0005-0002" in skus

    def test_find_by_pattern_tag(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.find_compatible_parts("gobilda_8mm_pattern")

        assert len(results) == 2  # channel and bracket

    def test_find_with_category_filter(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.find_compatible_parts("gobilda_8mm_pattern", category="structure/channel")

        assert len(results) == 1
        assert results[0]["sku"] == "1120-0001-0288"

    def test_find_no_results(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        results = engine.find_compatible_parts("nonexistent_tag")

        assert results == []


class TestSuggestMates:
    def test_suggest_channel_to_bracket(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        suggestions = engine.suggest_mates("1120-0001-0288", "1141-0001-0001")

        assert len(suggestions) > 0
        # Should suggest coincident mate based on matching M4 8mm-pitch hole patterns
        types = {s["type"] for s in suggestions}
        assert "coincident" in types

    def test_suggest_channel_to_wheel(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        suggestions = engine.suggest_mates("1120-0001-0288", "2900-0005-0002")

        assert len(suggestions) > 0
        # Should suggest concentric mate based on REX_8mm_shaft compatibility
        types = {s["type"] for s in suggestions}
        assert "concentric" in types

    def test_suggest_no_mates_for_unknown(self, profiles_dir):
        engine = PartsQuery(profiles_dir)
        engine.load()

        suggestions = engine.suggest_mates("1120-0001-0288", "9999-9999-9999")

        assert suggestions == []
