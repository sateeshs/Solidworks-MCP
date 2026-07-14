"""Component pattern operations mixin for SolidWorks COM automation.

Provides linear and circular component patterns via IFeatureManager.

Requires parent class (SolidWorksAutomation base) to provide:
- get_active_doc()
- _result()
- _units
"""

import logging
import math
import traceback

from ..constants import SwErrors, SwSelectType

logger = logging.getLogger(__name__)


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
            components: Names of components to pattern.
            direction_x, direction_y, direction_z: Primary direction vector.
            count: Number of instances in primary direction.
            spacing: Spacing between instances in user units.
            count2: Number of instances in secondary direction (1 = no 2nd direction).
            spacing2: Spacing in secondary direction in user units.
            direction2_x, direction2_y, direction2_z: Secondary direction vector.

        Returns:
            Result dict.
        """
        try:
            doc, err = self.get_active_doc()
            if err:
                return err

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

            # Select components
            doc.ClearSelection2(True)
            for i, comp_name in enumerate(components):
                append = i > 0
                selected = doc.Extension.SelectByID2(
                    comp_name, SwSelectType.COMPONENT,
                    0, 0, 0, append, 0, None, 0,
                )
                if not selected:
                    return self._result(
                        False,
                        f"Could not select component: {comp_name}",
                        SwErrors.swSelectionError,
                    )

            spacing_m = self._units.to_meters(spacing)
            spacing2_m = self._units.to_meters(spacing2)

            feat_mgr = doc.FeatureManager
            pattern = feat_mgr.FeatureLinearPattern4(
                count,                  # D1 total instances
                spacing_m,              # D1 spacing
                direction_x,            # D1 direction X
                direction_y,            # D1 direction Y
                direction_z,            # D1 direction Z
                False,                  # D1 reverse
                count2,                 # D2 total instances
                spacing2_m,            # D2 spacing
                direction2_x,           # D2 direction X
                direction2_y,           # D2 direction Y
                direction2_z,           # D2 direction Z
                False,                  # D2 reverse
                True,                   # Geometry pattern
                False,                  # Propagate visual
                False,                  # Vary sketch
            )

            if pattern is None:
                return self._result(
                    False,
                    "Failed to create linear pattern.",
                    SwErrors.swFeatureError,
                )

            total = count * count2
            logger.info(
                "Created linear pattern: %d x %d = %d instances of %s",
                count, count2, total, components,
            )
            return self._result(
                True,
                f"Linear pattern created: {total} instances",
                data={
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
            components: Names of components to pattern.
            axis_x, axis_y, axis_z: Rotation axis direction vector.
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

            # Select components
            doc.ClearSelection2(True)
            for i, comp_name in enumerate(components):
                append = i > 0
                selected = doc.Extension.SelectByID2(
                    comp_name, SwSelectType.COMPONENT,
                    0, 0, 0, append, 0, None, 0,
                )
                if not selected:
                    return self._result(
                        False,
                        f"Could not select component: {comp_name}",
                        SwErrors.swSelectionError,
                    )

            if equal_spacing:
                total_angle_rad = 2 * math.pi
            else:
                total_angle_rad = math.radians(angle if angle is not None else 360.0)

            feat_mgr = doc.FeatureManager
            pattern = feat_mgr.FeatureCircularPattern4(
                count,                  # Number of instances
                total_angle_rad,        # Total angle
                False,                  # Reverse direction
                "True" if equal_spacing else "False",  # Equal spacing string
                axis_x,                 # Axis X
                axis_y,                 # Axis Y
                axis_z,                 # Axis Z
                True,                   # Geometry pattern
                False,                  # Propagate visual
                False,                  # Vary sketch
            )

            if pattern is None:
                return self._result(
                    False,
                    "Failed to create circular pattern.",
                    SwErrors.swFeatureError,
                )

            angle_per = math.degrees(total_angle_rad) / count
            logger.info(
                "Created circular pattern: %d instances at %.1f deg spacing of %s",
                count, angle_per, components,
            )
            return self._result(
                True,
                f"Circular pattern created: {count} instances at {angle_per:.1f} deg spacing",
                data={
                    "count": count,
                    "total_angle_deg": math.degrees(total_angle_rad),
                    "angle_per_instance_deg": angle_per,
                    "components": components,
                },
            )
        except Exception as e:
            logger.error("create_circular_pattern error: %s\n%s", e, traceback.format_exc())
            return self._result(False, f"Error creating circular pattern: {e}",
                                SwErrors.swFeatureError)
