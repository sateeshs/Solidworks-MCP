"""Tests for solidworks_mcp.automation.materials.

COM calls are mocked. These pin the live-verified behaviour: SetMaterialPropertyName2
returns nothing and silently ignores bad names, so success is judged by reading
back MaterialIdName, and names are resolved case-insensitively from .sldmat XML.
"""

from unittest.mock import MagicMock

import pytest

from solidworks_mcp.automation.materials import (
    MaterialOperations, load_material_catalog, resolve_material,
)
from solidworks_mcp.constants import SwErrors

SLDMAT = """<?xml version="1.0" encoding="utf-16"?>
<mstns:materials xmlns:mstns="http://www.solidworks.com/sldmaterials">
  <classification name="Aluminium Alloys">
    <material name="6061 Alloy" matid="21">
      <physicalproperties>
        <EX displayname="Elastic modulus" value="69000000000.0" />
        <DENS displayname="Mass density" value="2700.0" />
        <SIGYLD displayname="Yield strength" value="55148500.0" />
      </physicalproperties>
    </material>
    <material name="6061-T6 (SS)" matid="22" />
  </classification>
  <classification name="Plastics">
    <material name="ABS" matid="33">
      <physicalproperties><DENS displayname="Mass density" value="1020.0" /></physicalproperties>
    </material>
    <material name="POM Acetal Copolymer" matid="40" />
  </classification>
</mstns:materials>
"""


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "SOLIDWORKS Materials.sldmat"
    path.write_text(SLDMAT, encoding="utf-16")
    return str(path)


class FakeAutomation(MaterialOperations):
    def __init__(self, db_paths, doc=None):
        self._doc = doc
        self._sw_app = MagicMock()
        self._sw_app.GetMaterialDatabases = tuple(db_paths)

    def get_active_doc(self):
        return self._doc, None

    def _result(self, success, message, error_code=SwErrors.swSuccess, data=None):
        result = {"success": success, "message": message, "error_code": int(error_code)}
        if data:
            result["data"] = data
        return result


def _part(applies=True, db_label="SOLIDWORKS Materials"):
    """Mock part whose MaterialIdName reflects SetMaterialPropertyName2 like SW does."""
    doc = MagicMock()
    doc.GetType = 1
    doc.MaterialIdName = ""
    doc.GetMassProperties = (0, 0, 0, 5e-5, 0.013, 0.135)

    def set_material(config, database, name):
        if applies:
            doc.MaterialIdName = f"{db_label}|{name}|1"

    doc.SetMaterialPropertyName2.side_effect = set_material
    return doc


class TestCatalog:
    def test_parses_utf16_sldmat(self, db_path):
        catalog = load_material_catalog([db_path])

        assert [m.name for m in catalog] == [
            "6061 Alloy", "6061-T6 (SS)", "ABS", "POM Acetal Copolymer"]
        alloy = catalog[0]
        assert alloy.classification == "Aluminium Alloys"
        assert alloy.database == "SOLIDWORKS Materials"
        assert dict(alloy.properties) == {
            "density_kg_m3": 2700.0,
            "elastic_modulus_pa": 69e9,
            "yield_strength_pa": 55148500.0,
        }

    def test_skips_missing_database(self, db_path, tmp_path):
        catalog = load_material_catalog([str(tmp_path / "gone.sldmat"), db_path])
        assert len(catalog) == 4


class TestResolve:
    def test_case_insensitive_match(self, db_path):
        entry, _ = resolve_material(load_material_catalog([db_path]), "abs")
        assert entry.name == "ABS"

    def test_database_filter_by_name(self, db_path):
        catalog = load_material_catalog([db_path])
        assert resolve_material(catalog, "ABS", "solidworks materials")[0] is not None
        entry, _ = resolve_material(catalog, "ABS", "Custom Materials")
        assert entry is None

    def test_miss_suggests_substring_matches(self, db_path):
        entry, suggestions = resolve_material(load_material_catalog([db_path]), "6061")
        assert entry is None
        assert suggestions[:2] == ["6061 Alloy", "6061-T6 (SS)"]


class TestApplyMaterial:
    def test_applies_resolved_name_with_full_db_path(self, db_path):
        doc = _part()
        result = FakeAutomation([db_path], doc).apply_material("6061 alloy")

        assert result["success"] is True
        doc.SetMaterialPropertyName2.assert_called_once_with("", db_path, "6061 Alloy")
        data = result["data"]
        assert data["material"] == "6061 Alloy"
        assert data["database"] == "SOLIDWORKS Materials"
        assert data["density_kg_m3"] == 2700.0
        assert data["mass_kg"] == pytest.approx(0.135)

    def test_unknown_material_never_calls_set(self, db_path):
        doc = _part()
        result = FakeAutomation([db_path], doc).apply_material("acetal")

        assert result["success"] is False
        assert result["error_code"] == SwErrors.swInvalidInput
        assert result["data"]["suggestions"] == ["POM Acetal Copolymer"]
        doc.SetMaterialPropertyName2.assert_not_called()

    def test_silent_set_failure_is_reported(self, db_path):
        result = FakeAutomation([db_path], _part(applies=False)).apply_material("ABS")

        assert result["success"] is False
        assert result["error_code"] == SwErrors.swFeatureError

    def test_rejects_non_part_document(self, db_path):
        doc = _part()
        doc.GetType = 2
        result = FakeAutomation([db_path], doc).apply_material("ABS")

        assert result["success"] is False
        assert result["error_code"] == SwErrors.swInvalidFileType
        doc.SetMaterialPropertyName2.assert_not_called()

    @pytest.mark.parametrize("name", ["", "   ", None])
    def test_requires_material_name(self, db_path, name):
        result = FakeAutomation([db_path], _part()).apply_material(name)
        assert result["error_code"] == SwErrors.swInvalidInput

    def test_no_readable_databases(self, tmp_path):
        result = FakeAutomation([str(tmp_path / "gone.sldmat")], _part()).apply_material("ABS")
        assert result["error_code"] == SwErrors.swFileNotFoundError
