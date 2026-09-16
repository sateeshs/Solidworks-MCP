"""Assembly operations mixin for SolidWorks COM automation.

Provides insert_component, insert_library_part, add_mate,
get_assembly_tree, and list_mates via IAssemblyDoc COM interface.

Requires parent class (SolidWorksAutomation base) to provide:
- get_active_doc()
- _result()
- _units
- _config (with gobilda_steps_path)
"""

import logging
import traceback
from typing import Optional

from ..constants import (
    SwDocumentTypes,
    SwErrors,
    SwMateAlign,
    SwMateTypes,
    SwSelectType,
)

logger = logging.getLogger(__name__)


class AssemblyOperations:
    """Mixin class for assembly operations on SolidWorks COM."""

    # ========================================================================
    # Assembly Creation
    # ========================================================================

    def create_assembly(self, name: str) -> dict:
        """Create a new empty assembly document.

        Args:
            name: Assembly name (without extension).

        Returns:
            Result dict with ``data.path`` on success.
        """
        try:
            if not self.is_connected:
                result = self.connect()
                if not result["success"]:
                    return result

            from ..utils import find_template
            template = find_template("assembly")
            if not template:
                return self._result(
                    False,
                    "Assembly template not found. Check SolidWorks installation.",
                    SwErrors.swTemplateNotFound,
                )

            doc = self._sw_app.NewDocument(
                template, 0, 0, 0
            )
            if doc is None:
                return self._result(
                    False,
                    "Failed to create assembly document.",
                    SwErrors.swFeatureError,
                )

            return self._result(
                True,
                f"Assembly '{name}' created.",
                data={"name": name},
            )
        except Exception as e:
            logger.error("create_assembly error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error creating assembly: {e}",
                                SwErrors.swFeatureError)

    # ========================================================================
    # Component Insertion
    # ========================================================================

    def insert_component(
        self,
        filepath: str,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> dict:
        """Insert a component from a file path into the active assembly.

        Args:
            filepath: Absolute path to the part/assembly file.
            position: (x, y, z) insertion point in user units.
            rotation: (rx, ry, rz) rotation angles in radians.

        Returns:
            Result dict with ``data.component_id`` on success.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            # Convert position to meters (SW internal unit)
            x = self._units.to_meters(position[0])
            y = self._units.to_meters(position[1])
            z = self._units.to_meters(position[2])

            component = doc.AddComponent5(
                filepath,               # ComponentPath
                0,                      # ConfigOption
                "",                     # ConfigName
                False,                  # UseConfigForPartProperties
                "",                     # NewConfigName
                x, y, z,               # X, Y, Z
            )

            if component is None:
                return self._result(
                    False,
                    f"Failed to insert component from {filepath}",
                    SwErrors.swFeatureError,
                )

            comp_name = _get_component_name(component)
            logger.info("Inserted component: %s", comp_name)

            return self._result(
                True,
                f"Component inserted: {comp_name}",
                data={"component_id": comp_name, "filepath": filepath},
            )
        except Exception as e:
            logger.error("insert_component error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error inserting component: {e}",
                                SwErrors.swFeatureError)

    def insert_library_part(
        self,
        sku: str,
        position: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> dict:
        """Insert a goBILDA library part by SKU.

        Resolves the SKU to a local STEP file path using the config's
        ``gobilda_steps_path``, then inserts via ``insert_component``.

        Args:
            sku: goBILDA part SKU (e.g. ``'1120-0001-0288'``).
            position: (x, y, z) insertion point in user units.
            rotation: (rx, ry, rz) rotation angles in radians.

        Returns:
            Result dict with ``data.component_id`` and ``data.sku``.
        """
        from ..parts.resolver import resolve_sku

        steps_root = self._config.gobilda_steps_path
        if not steps_root:
            return self._result(
                False,
                "gobilda_steps_path not configured. Set it in config.json.",
                SwErrors.swFileNotFoundError,
            )

        resolved = resolve_sku(sku, steps_root)
        if resolved is None:
            return self._result(
                False,
                f"SKU '{sku}' not found in {steps_root}",
                SwErrors.swFileNotFoundError,
            )

        if not resolved.exists:
            return self._result(
                False,
                f"STEP file missing for SKU '{sku}': {resolved.file_path}",
                SwErrors.swFileNotFoundError,
            )

        result = self.insert_component(resolved.file_path, position, rotation)
        if result["success"] and "data" in result:
            result["data"]["sku"] = sku
        return result

    # ========================================================================
    # Mate Constraints
    # ========================================================================

    def add_mate(
        self,
        mate_type: str | int,
        entity1: str,
        entity2: str,
        value: float = 0.0,
        alignment: int = SwMateAlign.swMateAlignCLOSEST,
    ) -> dict:
        """Add a mate constraint between two entities.

        Args:
            mate_type: Mate type — string (``'coincident'``, ``'concentric'``,
                       ``'distance'``, etc.) or ``SwMateTypes`` int.
            entity1: Selection name of the first entity
                     (e.g. ``'Face<1>@channel-1'``).
            entity2: Selection name of the second entity.
            value: Distance or angle value (for distance/angle mates),
                   in user units.
            alignment: Mate alignment option.

        Returns:
            Result dict.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            # Resolve mate type
            mate_int = _resolve_mate_type(mate_type)
            if mate_int is None:
                return self._result(
                    False,
                    f"Invalid mate type: {mate_type}",
                    SwErrors.swInvalidInput,
                )

            # Convert value to meters for distance mates
            sw_value = value
            if mate_int == SwMateTypes.swMateDISTANCE:
                sw_value = self._units.to_meters(value)

            # Select entities
            doc.ClearSelection2(True)

            selected1 = doc.Extension.SelectByID2(
                entity1, "", 0, 0, 0, False, 1, None, 0
            )
            if not selected1:
                return self._result(
                    False,
                    f"Could not select entity: {entity1}",
                    SwErrors.swSelectionError,
                )

            selected2 = doc.Extension.SelectByID2(
                entity2, "", 0, 0, 0, True, 1, None, 0
            )
            if not selected2:
                return self._result(
                    False,
                    f"Could not select entity: {entity2}",
                    SwErrors.swSelectionError,
                )

            # Add the mate
            error_code = 0
            mate_feature = doc.AddMate5(
                mate_int,           # Type
                alignment,          # Alignment
                False,              # Flip
                sw_value,           # Distance/angle value
                sw_value,           # Min value (unused for basic mates)
                sw_value,           # Max value (unused for basic mates)
                0,                  # Distance2
                0,                  # Distance2 min
                0,                  # Distance2 max
                0,                  # Angle for distance mates
                False,              # ForPositioningOnly
                False,              # LockRotation
                error_code,         # Error status (out param via COM)
            )

            if mate_feature is None:
                return self._result(
                    False,
                    f"Failed to add {mate_type} mate between {entity1} and {entity2}",
                    SwErrors.swFeatureError,
                )

            logger.info("Added %s mate: %s <-> %s", mate_type, entity1, entity2)
            return self._result(
                True,
                f"Added {mate_type} mate: {entity1} <-> {entity2}",
                data={
                    "mate_type": str(mate_type),
                    "entity1": entity1,
                    "entity2": entity2,
                },
            )
        except Exception as e:
            logger.error("add_mate error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error adding mate: {e}",
                                SwErrors.swFeatureError)

    # ========================================================================
    # Assembly Inspection
    # ========================================================================

    def get_assembly_tree(self) -> dict:
        """Get the component tree of the active assembly.

        Returns:
            Result dict with ``data.components`` list.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            components = []
            try:
                root_comp = doc.ConfigurationManager.ActiveConfiguration.GetRootComponent3(True)
            except Exception:
                return self._result(
                    False,
                    "Active document is not an assembly.",
                    SwErrors.swFeatureError,
                )

            if root_comp is None:
                return self._result(
                    False,
                    "Could not access assembly root component.",
                    SwErrors.swFeatureError,
                )

            children = root_comp.GetChildren()
            if children:
                for child in children:
                    comp_info = _extract_component_info(child)
                    components.append(comp_info)

            return self._result(
                True,
                f"Assembly tree: {len(components)} components",
                data={"components": components, "count": len(components)},
            )
        except Exception as e:
            logger.error("get_assembly_tree error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error reading assembly tree: {e}",
                                SwErrors.swFeatureError)

    def list_mates(self) -> dict:
        """List all mate constraints in the active assembly.

        Returns:
            Result dict with ``data.mates`` list.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            mates = []
            try:
                mate_group = doc.FeatureByName("MateGroup")
            except Exception:
                mate_group = None

            if mate_group is None:
                return self._result(
                    True,
                    "No mates found.",
                    data={"mates": [], "count": 0},
                )

            sub_features = mate_group.GetChildren()
            if sub_features:
                for feat in sub_features:
                    mate_info = _extract_mate_info(feat)
                    if mate_info:
                        mates.append(mate_info)

            return self._result(
                True,
                f"Found {len(mates)} mates",
                data={"mates": mates, "count": len(mates)},
            )
        except Exception as e:
            logger.error("list_mates error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error listing mates: {e}",
                                SwErrors.swFeatureError)


# ============================================================================
# Private helpers
# ============================================================================

_MATE_TYPE_MAP: dict[str, int] = {
    "coincident": SwMateTypes.swMateCOINCIDENT,
    "concentric": SwMateTypes.swMateCONCENTRIC,
    "perpendicular": SwMateTypes.swMatePERPENDICULAR,
    "parallel": SwMateTypes.swMatePARALLEL,
    "tangent": SwMateTypes.swMateTANGENT,
    "distance": SwMateTypes.swMateDISTANCE,
    "angle": SwMateTypes.swMateANGLE,
    "lock": SwMateTypes.swMateLOCK,
    "width": SwMateTypes.swMateWIDTH,
}


def _resolve_mate_type(mate_type: str | int) -> int | None:
    """Convert a mate type string or int to SwMateTypes value."""
    if isinstance(mate_type, int):
        try:
            SwMateTypes(mate_type)
            return mate_type
        except ValueError:
            return None
    if isinstance(mate_type, str):
        return _MATE_TYPE_MAP.get(mate_type.lower())
    return None


def _get_component_name(component) -> str:
    """Safely extract the name from a COM component object."""
    try:
        name = component.Name2
        if callable(name):
            return name()
        return str(name)
    except Exception:
        try:
            name = component.Name
            if callable(name):
                return name()
            return str(name)
        except Exception:
            return "unknown"


def _extract_component_info(component) -> dict:
    """Extract basic info from a COM IComponent2 object."""
    name = _get_component_name(component)
    try:
        suppressed = component.IsSuppressed()
    except Exception:
        suppressed = False

    try:
        visible = component.Visible
        if callable(visible):
            visible = visible()
    except Exception:
        visible = True

    try:
        path = component.GetPathName()
    except Exception:
        path = ""

    return {
        "name": name,
        "suppressed": bool(suppressed),
        "visible": bool(visible),
        "path": str(path),
    }


def _extract_mate_info(feature) -> dict | None:
    """Extract info from a mate feature."""
    try:
        name = feature.Name
        if callable(name):
            name = name()

        type_name = feature.GetTypeName2
        if callable(type_name):
            type_name = type_name()

        return {
            "name": str(name),
            "type": str(type_name),
        }
    except Exception:
        return None
