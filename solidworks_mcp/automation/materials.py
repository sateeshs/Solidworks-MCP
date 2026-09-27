"""
SolidWorks Material Operations
------------------------------
Assign materials to parts from the installed SolidWorks material databases.

Live-verified 2026-09-26 (SW 34.4.1, win32com dynamic dispatch):
- IPartDoc.SetMaterialPropertyName2(config, database, name) works and returns
  None. It silently ignores an unknown or wrongly-cased material name, so the
  result has to be checked by reading back IPartDoc.MaterialIdName
  ("<database>|<material>|<id>").
- IPartDoc.GetMaterialPropertyName2 fails with "Type mismatch" (it has a ByRef
  out-param), so MaterialIdName is the only usable getter.
- The database argument accepts the full .sldmat path, which is what
  ISldWorks.GetMaterialDatabases returns, so we always pass that.
- Material names are case-sensitive. We resolve the user's input against the
  .sldmat files (UTF-16 XML) first so matching is case-insensitive and a miss
  comes back with suggestions.
"""

import difflib
import logging
import os
import traceback
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional, Sequence, Tuple

from ..constants import SwErrors, SwDocumentTypes

logger = logging.getLogger(__name__)

# Physical properties reported back, keyed by their .sldmat tag (SI units)
_REPORTED_PROPS = {
    "DENS": "density_kg_m3",
    "EX": "elastic_modulus_pa",
    "NUXY": "poissons_ratio",
    "SIGYLD": "yield_strength_pa",
    "SIGXT": "tensile_strength_pa",
}


@dataclass(frozen=True)
class MaterialEntry:
    """One material from a .sldmat database"""
    name: str
    classification: str
    database: str
    path: str
    properties: Tuple[Tuple[str, float], ...] = ()


def _database_name(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


@lru_cache(maxsize=32)
def _parse_database(path: str, mtime: float) -> Tuple[MaterialEntry, ...]:
    """Parse one .sldmat file. mtime is part of the cache key only."""
    root = ET.parse(path).getroot()
    entries = []
    for cls in root.iter("classification"):
        for mat in cls.findall("material"):
            props = []
            phys = mat.find("physicalproperties")
            if phys is not None:
                for tag, key in _REPORTED_PROPS.items():
                    el = phys.find(tag)
                    try:
                        props.append((key, float(el.get("value"))))
                    except (AttributeError, TypeError, ValueError):
                        pass
            entries.append(MaterialEntry(
                name=mat.get("name", ""),
                classification=cls.get("name", ""),
                database=_database_name(path),
                path=path,
                properties=tuple(props),
            ))
    return tuple(entries)


def load_material_catalog(paths: Sequence[str]) -> List[MaterialEntry]:
    """Load every material from the given .sldmat files, skipping unreadable ones"""
    catalog: List[MaterialEntry] = []
    for path in paths or ():
        try:
            catalog.extend(_parse_database(path, os.path.getmtime(path)))
        except (OSError, ET.ParseError) as e:
            logger.debug(f"Skipping material database {path}: {e}")
    return catalog


def resolve_material(catalog: Sequence[MaterialEntry], name: str,
                     database: Optional[str] = None
                     ) -> Tuple[Optional[MaterialEntry], List[str]]:
    """
    Find a material by name (exact match first, then case-insensitive)

    Args:
        catalog: Entries from load_material_catalog
        name: Material name as the user typed it
        database: Optional database name (e.g. "SOLIDWORKS Materials") or path

    Returns:
        (entry, []) on a match, or (None, suggested names) on a miss
    """
    candidates = list(catalog)
    if database:
        wanted = database.casefold()
        candidates = [m for m in candidates
                      if m.database.casefold() == wanted or m.path.casefold() == wanted]

    for m in candidates:
        if m.name == name:
            return m, []
    key = name.casefold()
    for m in candidates:
        if m.name.casefold() == key:
            return m, []

    names = list(dict.fromkeys(m.name for m in candidates))
    suggestions = [n for n in names if key and key in n.casefold()]
    suggestions += [n for n in difflib.get_close_matches(name, names, n=8, cutoff=0.5)
                    if n not in suggestions]
    return None, suggestions[:8]


class MaterialOperations:
    """Material assignment operations mixin"""

    def apply_material(self, material: str, database: Optional[str] = None) -> Dict:
        """
        Apply a material to the active part (active configuration)

        Args:
            material: Material name, e.g. "6061 Alloy", "ABS" (case-insensitive)
            database: Optional database to restrict the lookup to,
                e.g. "SOLIDWORKS Materials" or "Custom Materials"

        Returns:
            Result dictionary
        """
        try:
            if not isinstance(material, str) or not material.strip():
                return self._result(False, "material name is required",
                                    SwErrors.swInvalidInput)
            material = material.strip()

            doc, err = self.get_active_doc()
            if err:
                return err

            if doc.GetType != SwDocumentTypes.swDocPART:
                return self._result(False,
                    "Materials can only be applied to a part. Open or activate a part document.",
                    SwErrors.swInvalidFileType)

            catalog = load_material_catalog(self._sw_app.GetMaterialDatabases)
            if not catalog:
                return self._result(False,
                    "No SolidWorks material databases could be read",
                    SwErrors.swFileNotFoundError)

            entry, suggestions = resolve_material(catalog, material, database)
            if entry is None:
                where = f" in database '{database}'" if database else ""
                hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                return self._result(False,
                    f"Material '{material}' not found{where}.{hint}",
                    SwErrors.swInvalidInput, {"suggestions": suggestions})

            doc.SetMaterialPropertyName2("", entry.path, entry.name)

            # Set returns nothing and ignores bad input, so read back to confirm
            material_id = doc.MaterialIdName or ""
            parts = material_id.split("|")
            if len(parts) < 2 or parts[1] != entry.name:
                return self._result(False,
                    f"SolidWorks did not apply '{entry.name}' (current material: "
                    f"'{material_id or 'none'}')",
                    SwErrors.swFeatureError)

            data = {
                "material": entry.name,
                "classification": entry.classification,
                "database": parts[0],
                **dict(entry.properties),
            }
            try:
                data["mass_kg"] = doc.GetMassProperties[5]
            except Exception as e:
                logger.debug(f"GetMassProperties after material change failed: {e}")

            message = f"Applied material '{entry.name}'"
            if "mass_kg" in data:
                message += f" - mass now {data['mass_kg']:.4f}kg"
            return self._result(True, message, SwErrors.swSuccess, data)

        except Exception as e:
            logger.error(f"Apply material error: {e}\n{traceback.format_exc()}")
            return self._result(False, f"Error: {e}", SwErrors.swFeatureError)
