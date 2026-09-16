"""SKU to STEP file path resolver.

Given a goBILDA SKU (e.g. '1120-0001-0288'), resolves to the absolute
STEP file path on the Windows machine (e.g. C:\\goBILDA\\channel\\1120-0001-0288.step).

Pure logic — no COM, no SolidWorks dependency. Fully testable on Linux.
"""

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Known STEP file extensions, in preference order
_STEP_EXTENSIONS = (".step", ".stp", ".STEP", ".STP")


@dataclass(frozen=True)
class ResolvedPart:
    """Result of resolving a SKU to a file path."""
    sku: str
    file_path: str
    category: str
    exists: bool


def resolve_sku(
    sku: str,
    steps_root: str,
    catalog_lookup: dict[str, str] | None = None,
) -> ResolvedPart | None:
    """Resolve a SKU to an absolute STEP file path.

    Resolution strategy (first match wins):
    1. If *catalog_lookup* maps the SKU to a ``source_file`` relative path,
       join it with *steps_root*.
    2. Walk subdirectories of *steps_root* looking for ``<sku>.step`` or
       ``<sku>.stp``.

    Args:
        sku: Part SKU string (e.g. ``'1120-0001-0288'``).
        steps_root: Root directory containing STEP files
                    (e.g. ``'C:\\goBILDA'``).
        catalog_lookup: Optional mapping of SKU -> ``source_file`` relative
                        paths from the catalog (e.g. ``'channel/1120-0001-0288.step'``).

    Returns:
        A ``ResolvedPart`` if the SKU can be resolved, or ``None`` if not found.
    """
    if not sku or not steps_root:
        return None

    sku = sku.strip()

    # Strategy 1: catalog provides relative path
    if catalog_lookup and sku in catalog_lookup:
        source_file = catalog_lookup[sku]
        abs_path = os.path.normpath(os.path.join(steps_root, source_file))

        # Prevent path traversal
        if not abs_path.startswith(os.path.normpath(steps_root)):
            logger.warning("Path traversal detected for SKU %s: %s", sku, source_file)
            return None

        category = _category_from_path(source_file)
        return ResolvedPart(
            sku=sku,
            file_path=abs_path,
            category=category,
            exists=os.path.isfile(abs_path),
        )

    # Strategy 2: scan subdirectories
    for dirpath, _dirnames, filenames in os.walk(steps_root):
        for ext in _STEP_EXTENSIONS:
            candidate = sku + ext
            if candidate in filenames:
                abs_path = os.path.join(dirpath, candidate)
                rel = os.path.relpath(dirpath, steps_root)
                category = rel.replace("\\", "/") if rel != "." else ""
                return ResolvedPart(
                    sku=sku,
                    file_path=abs_path,
                    category=category,
                    exists=True,
                )

    logger.info("SKU %s not found under %s", sku, steps_root)
    return None


def build_catalog_lookup(catalog_entries: list[dict]) -> dict[str, str]:
    """Build a SKU -> source_file mapping from catalog data.

    Args:
        catalog_entries: List of catalog entry dicts, each with at least
                         ``sku`` and ``source_file`` keys.

    Returns:
        A dict mapping SKU strings to relative file paths.
    """
    lookup: dict[str, str] = {}
    for entry in catalog_entries:
        sku = entry.get("sku", "")
        source = entry.get("source_file", "")
        if sku and source:
            lookup[sku] = source
    return lookup


def _category_from_path(source_file: str) -> str:
    """Extract category from a source_file relative path.

    ``'channel/1120-0001-0288.step'`` -> ``'channel'``
    ``'1120-0001-0288.step'`` -> ``''``
    """
    parts = source_file.replace("\\", "/").split("/")
    if len(parts) > 1:
        return "/".join(parts[:-1])
    return ""
