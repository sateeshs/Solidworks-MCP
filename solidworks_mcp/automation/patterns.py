"""Component pattern operations mixin for SolidWorks COM automation.

Provides linear and circular component patterns (LocalLPattern /
LocalCirPattern) via IFeatureManager.CreateDefinition + CreateFeature.

The pattern feature data objects don't accept entity references through
late-bound property puts on this binding (D1Axis/Axis silently stay unset),
so directions, axes and seeds are passed via selection marks instead:

- Linear:   seeds mark 1, direction 1 mark 2, direction 2 mark 4
- Circular: seeds mark 1, axis mark 2

SolidWorks has no vector-direction input for these features, so direction
vectors must be axis-aligned: they map to the assembly's default reference
planes (plane normals) and, for circular patterns, to a reference axis at the
intersection of two default planes.

Requires parent class (SolidWorksAutomation base) to provide:
- get_active_doc()
- _result()
- _units
"""

import logging
import math
import traceback

from ..constants import SwErrors
from .assemblies import _com_get

logger = logging.getLogger(__name__)

# swFeatureNameID_e
_SW_FM_LOCAL_LINEAR_PATTERN = 108
_SW_FM_LOCAL_CIRCULAR_PATTERN = 109

_MARK_SEED = 1
_MARK_DIRECTION1 = 2
_MARK_DIRECTION2 = 4
_MARK_CIRCULAR_AXIS = 2

# Default reference planes in tree order and the world axis each is normal to.
_DEFAULT_PLANE_NORMALS = (("Front", 2), ("Top", 1), ("Right", 0))
_AXIS_LABELS = "XYZ"


class PatternOperations:
    """Mixin class for component pattern operations."""

    def create_linear_pattern(
        self,
        components: list[str],
        direction_x: float = 1.0,
        direction_y: float = 0.0,
        direction_z: float = 0.0,
        count: int = 2,
        spacing: float = 50.0,
        count2: int = 1,
        spacing2: float = 50.0,
        direction2_x: float = 0.0,
        direction2_y: float = 1.0,
        direction2_z: float = 0.0,
    ) -> dict:
        """Create a linear pattern of assembly components.

        Args:
            components: Names of components to pattern (e.g. ``Part1-1``).
            direction_x, direction_y, direction_z: Primary direction; must be
                axis-aligned (e.g. 0,1,0 or -1,0,0).
            count: Number of instances in primary direction (including seed).
            spacing: Spacing between instances in user units.
            count2: Number of instances in secondary direction (1 = no 2nd direction).
            spacing2: Spacing in secondary direction in user units.
            direction2_x, direction2_y, direction2_z: Secondary direction;
                must be axis-aligned.

        Returns:
            Result dict.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            err = self._validate_pattern_input(components, count)
            if err:
                return err

            dir1 = _axis_of((direction_x, direction_y, direction_z))
            if dir1 is None:
                return self._result(
                    False,
                    "Primary direction must be axis-aligned (e.g. 1,0,0 or 0,-1,0).",
                    SwErrors.swInvalidInput,
                )
            dir2 = None
            if count2 > 1:
                dir2 = _axis_of((direction2_x, direction2_y, direction2_z))
                if dir2 is None:
                    return self._result(
                        False,
                        "Secondary direction must be axis-aligned (e.g. 0,1,0).",
                        SwErrors.swInvalidInput,
                    )

            planes = _default_planes(doc)
            if planes is None:
                return self._result(
                    False,
                    "Could not find the assembly's default reference planes.",
                    SwErrors.swFeatureError,
                )

            doc.ClearSelection2(True)
            if not planes[dir1[0]].Select2(False, _MARK_DIRECTION1):
                return self._result(False, "Could not select primary direction plane.",
                                    SwErrors.swSelectionError)
            if dir2 is not None and not planes[dir2[0]].Select2(True, _MARK_DIRECTION2):
                return self._result(False, "Could not select secondary direction plane.",
                                    SwErrors.swSelectionError)
            err = self._select_seed_components(doc, components)
            if err:
                return err

            feat_mgr = doc.FeatureManager
            data = feat_mgr.CreateDefinition(_SW_FM_LOCAL_LINEAR_PATTERN)
            data.D1TotalInstances = count
            data.D1Spacing = self._units.to_meters(spacing)
            data.D1ReverseDirection = dir1[1] < 0
            if dir2 is not None:
                data.D2TotalInstances = count2
                data.D2Spacing = self._units.to_meters(spacing2)
                data.D2ReverseDirection = dir2[1] < 0

            pattern = feat_mgr.CreateFeature(data)
            doc.ClearSelection2(True)
            if pattern is None:
                return self._result(
                    False,
                    "Failed to create linear pattern.",
                    SwErrors.swFeatureError,
                )

            if dir2 is None:
                count2 = 1
            total = count * count2
            name = str(_com_get(pattern, "Name"))
            logger.info(
                "Created linear pattern %s: %d x %d = %d instances of %s",
                name, count, count2, total, components,
            )
            return self._result(
                True,
                f"Linear pattern created: {total} instances",
                data={
                    "feature": name,
                    "count_d1": count,
                    "spacing_d1": spacing,
                    "count_d2": count2,
                    "spacing_d2": spacing2,
                    "total": total,
                    "components": components,
                },
            )
        except Exception as e:
            logger.error("create_linear_pattern error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error creating linear pattern: {e}",
                                SwErrors.swFeatureError)

    def create_circular_pattern(
        self,
        components: list[str],
        axis_x: float = 0.0,
        axis_y: float = 1.0,
        axis_z: float = 0.0,
        count: int = 4,
        angle: float | None = None,
        equal_spacing: bool = True,
    ) -> dict:
        """Create a circular pattern of assembly components.

        Args:
            components: Names of components to pattern (e.g. ``Part1-1``).
            axis_x, axis_y, axis_z: Rotation axis through the assembly origin;
                must be axis-aligned (a sign flip reverses the rotation).
            count: Number of instances (including the seed).
            angle: Total angle in degrees. Ignored if ``equal_spacing`` is True
                   (defaults to 360).
            equal_spacing: Distribute instances equally over 360 degrees.

        Returns:
            Result dict.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

            err = self._validate_pattern_input(components, count)
            if err:
                return err

            axis = _axis_of((axis_x, axis_y, axis_z))
            if axis is None:
                return self._result(
                    False,
                    "Rotation axis must be axis-aligned (e.g. 0,1,0 or 0,0,-1).",
                    SwErrors.swInvalidInput,
                )

            axis_feat = _reference_axis(doc, axis[0])
            if axis_feat is None:
                return self._result(
                    False,
                    f"Could not create a reference axis along {_AXIS_LABELS[axis[0]]}.",
                    SwErrors.swFeatureError,
                )

            if equal_spacing:
                total_angle_rad = 2 * math.pi
            else:
                total_angle_rad = math.radians(angle if angle is not None else 360.0)

            doc.ClearSelection2(True)
            if not axis_feat.Select2(False, _MARK_CIRCULAR_AXIS):
                return self._result(False, "Could not select rotation axis.",
                                    SwErrors.swSelectionError)
            err = self._select_seed_components(doc, components)
            if err:
                return err

            total_deg = math.degrees(total_angle_rad)
            # A full circle wraps back onto the seed; a partial arc includes both ends.
            full_circle = math.isclose(total_deg, 360.0)
            gaps = count if full_circle else count - 1
            angle_per = total_deg / gaps

            feat_mgr = doc.FeatureManager
            data = feat_mgr.CreateDefinition(_SW_FM_LOCAL_CIRCULAR_PATTERN)
            data.TotalInstances = count
            # With EqualSpacing, SolidWorks always spreads over 360° and ignores
            # Spacing, so partial arcs must give the per-instance angle instead.
            data.EqualSpacing = full_circle
            data.Spacing = total_angle_rad if full_circle else math.radians(angle_per)
            data.ReverseDirection = axis[1] < 0

            pattern = feat_mgr.CreateFeature(data)
            doc.ClearSelection2(True)
            if pattern is None:
                return self._result(
                    False,
                    "Failed to create circular pattern.",
                    SwErrors.swFeatureError,
                )

            name = str(_com_get(pattern, "Name"))
            logger.info(
                "Created circular pattern %s: %d instances at %.1f deg spacing of %s",
                name, count, angle_per, components,
            )
            return self._result(
                True,
                f"Circular pattern created: {count} instances at {angle_per:.1f} deg spacing",
                data={
                    "feature": name,
                    "axis": _AXIS_LABELS[axis[0]],
                    "count": count,
                    "total_angle_deg": total_deg,
                    "angle_per_instance_deg": angle_per,
                    "components": components,
                },
            )
        except Exception as e:
            logger.error("create_circular_pattern error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error creating circular pattern: {e}",
                                SwErrors.swFeatureError)

    def _validate_pattern_input(self, components: list[str], count: int) -> dict | None:
        if not components:
            return self._result(
                False,
                "No components specified for pattern.",
                SwErrors.swInvalidInput,
            )
        if count < 2:
            return self._result(
                False,
                "Pattern count must be >= 2.",
                SwErrors.swInvalidInput,
            )
        return None

    def _select_seed_components(self, doc, components: list[str]) -> dict | None:
        """Append each component to the selection with the seed mark."""
        sel_mgr = doc.SelectionManager
        for comp_name in components:
            # Accept "Part1-1" as well as full select IDs like "Part1-1@Assem1"
            comp = doc.GetComponentByName(comp_name.split("@")[0])
            select_data = _com_get(sel_mgr, "CreateSelectData")
            select_data.Mark = _MARK_SEED
            if comp is None or not comp.Select4(True, select_data, False):
                doc.ClearSelection2(True)
                return self._result(
                    False,
                    f"Could not select component: {comp_name}",
                    SwErrors.swSelectionError,
                )
        return None


def _axis_of(vector: tuple[float, float, float]) -> tuple[int, int] | None:
    """Return (axis_index, sign) for an axis-aligned vector, else None."""
    nonzero = [(i, v) for i, v in enumerate(vector) if abs(v) > 1e-9]
    if len(nonzero) != 1:
        return None
    index, value = nonzero[0]
    return index, (1 if value > 0 else -1)


def _default_planes(doc) -> dict | None:
    """Map world axis index -> the default reference plane normal to it.

    Found by type/tree order rather than name, since plane names are localized.
    """
    ref_planes = [
        feat for feat in doc.FeatureManager.GetFeatures(True) or []
        if _com_get(feat, "GetTypeName2") == "RefPlane"
    ]
    if len(ref_planes) < 3:
        return None
    return {axis: ref_planes[i] for i, (_, axis) in enumerate(_DEFAULT_PLANE_NORMALS)}


def _reference_axis(doc, axis_index: int):
    """Return a reference axis along a world axis, creating it if needed.

    The axis is the intersection of the two default planes whose normals are
    the other two world axes. Created axes are named "MCP Axis X/Y/Z" and reused.
    """
    name = f"MCP Axis {_AXIS_LABELS[axis_index]}"
    existing = doc.FeatureByName(name)
    if existing is not None:
        return existing

    planes = _default_planes(doc)
    if planes is None:
        return None
    others = [i for i in range(3) if i != axis_index]

    before = {
        str(_com_get(feat, "Name"))
        for feat in doc.FeatureManager.GetFeatures(True) or []
    }
    doc.ClearSelection2(True)
    planes[others[0]].Select2(False, 0)
    planes[others[1]].Select2(True, 0)
    created = doc.InsertAxis2(True)
    doc.ClearSelection2(True)
    if not created:
        return None

    for feat in doc.FeatureManager.GetFeatures(True) or []:
        if (_com_get(feat, "GetTypeName2") == "RefAxis"
                and str(_com_get(feat, "Name")) not in before):
            feat.Name = name
            return feat
    return None
