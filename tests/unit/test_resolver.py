"""Tests for solidworks_mcp.parts.resolver — SKU to STEP path resolution."""

import os

import pytest

from solidworks_mcp.parts.resolver import (
    ResolvedPart,
    build_catalog_lookup,
    resolve_sku,
    _category_from_path,
)


class TestResolveSkuWithCatalog:
    """Strategy 1: resolve via catalog_lookup."""

    def test_resolves_known_sku(self, tmp_path):
        # Arrange
        channel_dir = tmp_path / "channel"
        channel_dir.mkdir()
        step_file = channel_dir / "1120-0001-0288.step"
        step_file.write_text("dummy")

        lookup = {"1120-0001-0288": "channel/1120-0001-0288.step"}

        # Act
        result = resolve_sku("1120-0001-0288", str(tmp_path), lookup)

        # Assert
        assert result is not None
        assert result.sku == "1120-0001-0288"
        assert result.exists is True
        assert result.category == "channel"
        assert result.file_path.endswith("1120-0001-0288.step")

    def test_marks_missing_file_as_not_exists(self, tmp_path):
        lookup = {"1120-0001-0288": "channel/1120-0001-0288.step"}
        result = resolve_sku("1120-0001-0288", str(tmp_path), lookup)

        assert result is not None
        assert result.exists is False

    def test_blocks_path_traversal(self, tmp_path):
        lookup = {"evil-sku": "../../../etc/passwd"}
        result = resolve_sku("evil-sku", str(tmp_path), lookup)

        assert result is None

    def test_strips_whitespace_from_sku(self, tmp_path):
        channel_dir = tmp_path / "channel"
        channel_dir.mkdir()
        (channel_dir / "1120-0001-0288.step").write_text("dummy")

        lookup = {"1120-0001-0288": "channel/1120-0001-0288.step"}
        result = resolve_sku("  1120-0001-0288  ", str(tmp_path), lookup)

        assert result is not None
        assert result.sku == "1120-0001-0288"


class TestResolveSkuByScan:
    """Strategy 2: resolve by scanning subdirectories."""

    def test_finds_step_in_subdirectory(self, tmp_path):
        motor_dir = tmp_path / "motors"
        motor_dir.mkdir()
        (motor_dir / "5202-0002-0019.step").write_text("dummy")

        result = resolve_sku("5202-0002-0019", str(tmp_path))

        assert result is not None
        assert result.sku == "5202-0002-0019"
        assert result.exists is True
        assert result.category == "motors"

    def test_finds_stp_extension(self, tmp_path):
        (tmp_path / "5202-0002-0019.stp").write_text("dummy")

        result = resolve_sku("5202-0002-0019", str(tmp_path))

        assert result is not None
        assert result.exists is True

    def test_returns_none_for_missing_sku(self, tmp_path):
        result = resolve_sku("9999-9999-9999", str(tmp_path))
        assert result is None


class TestResolveSkuEdgeCases:
    """Edge cases and invalid inputs."""

    def test_empty_sku_returns_none(self, tmp_path):
        assert resolve_sku("", str(tmp_path)) is None

    def test_empty_steps_root_returns_none(self):
        assert resolve_sku("1120-0001-0288", "") is None

    def test_none_sku_returns_none(self, tmp_path):
        assert resolve_sku(None, str(tmp_path)) is None


class TestBuildCatalogLookup:
    """Tests for building SKU -> source_file mappings."""

    def test_builds_from_entries(self):
        entries = [
            {"sku": "1120-0001-0288", "source_file": "channel/1120-0001-0288.step"},
            {"sku": "2900-0005-0002", "source_file": "wheels/2900-0005-0002.step"},
        ]
        lookup = build_catalog_lookup(entries)

        assert lookup["1120-0001-0288"] == "channel/1120-0001-0288.step"
        assert lookup["2900-0005-0002"] == "wheels/2900-0005-0002.step"
        assert len(lookup) == 2

    def test_skips_entries_without_sku(self):
        entries = [{"source_file": "channel/foo.step"}]
        lookup = build_catalog_lookup(entries)
        assert len(lookup) == 0

    def test_skips_entries_without_source_file(self):
        entries = [{"sku": "1120-0001-0288"}]
        lookup = build_catalog_lookup(entries)
        assert len(lookup) == 0

    def test_empty_list(self):
        assert build_catalog_lookup([]) == {}


class TestCategoryFromPath:
    """Tests for _category_from_path helper."""

    def test_single_level(self):
        assert _category_from_path("channel/1120-0001-0288.step") == "channel"

    def test_multi_level(self):
        assert _category_from_path("structure/channel/foo.step") == "structure/channel"

    def test_no_directory(self):
        assert _category_from_path("1120-0001-0288.step") == ""

    def test_backslash_normalized(self):
        assert _category_from_path("channel\\1120-0001-0288.step") == "channel"


class TestResolvedPartImmutable:
    """Verify ResolvedPart is frozen."""

    def test_cannot_mutate(self):
        rp = ResolvedPart(sku="test", file_path="/tmp/test.step",
                          category="channel", exists=True)
        with pytest.raises(AttributeError):
            rp.sku = "changed"
