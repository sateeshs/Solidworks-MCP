# SolidWorks Modeling Skills Notes

> **Purpose:** Organize frequently used SOLIDWORKS modeling techniques focused on "stability, maintainability, and efficiency" into a reusable checklist. The content is synthesized and summarized from public tutorials (not verbatim excerpts).

---

## 1) Sketches and Design Intent

- **Keep sketches "lean and stable":** If a shape can be expressed using multiple simple sketches/features, avoid packing too much geometry into a single sketch.
- **Fully Define whenever possible:** Use dimensions and relations to stabilize critical geometry.
- **Avoid "daisy chaining":** Do not let A drive B, B drive C, etc. A more stable approach is to have A directly drive both B and C.

---

## 2) Mirroring: Mirror Entities vs. Dynamic Mirror

- **Mirror Entities:** Best used after the sketch is finished. Relies on a "mirror centerline + selected entities to mirror."
- **Dynamic Mirror:** Best used while drawing. Select the centerline or model edge first to enter dynamic mirror mode, then start sketching.
- **Maintain symmetry with mirrors:** Prioritize mirrors or midplanes for symmetrical structures to ensure future modify-ability.

---

## 3) Reference Geometry: Common Uses of Reference Planes

- **Offset Plane:** Offset by a distance from a face/plane, used for "sketching/cuts near a surface" or local features.
- **Angle Plane:** Requires a face/plane + a rotation axis (model edge or sketch line).
- **Mid Plane:** Generated midway between two faces; commonly used to establish symmetrical mirror planes.
- **Cylindrical Surface Plane:** Used for cutting or positioning on cylindrical surfaces (may require extra selections to determine direction).

---

## 4) Organization of Fillets/Chamfers (Stability and Failure Rates)

- **Leave large-scale fillets toward the end:** Stabilize the main body (extrudes, lofts, revolves) first, then add fillet details.
- **Use FilletXpert when adjusting/repairing fillets:**
  - `Add`: Batch-add fillets without exiting the PropertyManager.
  - `Change`: Uniformly change radii or delete specific fillets.
  - `Corner`: Handle three-fillet intersections or copy corner conditions.

---

## 5) External References and Circular References

- **Top-down design is great for early-stage rapid design**; once the design is finalized, **it is recommended to replace external references with dimensions/relations** so parts become "self-contained."
- **Do not blindly "Break References":** Many tutorials suggest a safer approach: "Replace Sketch Plane / Replace Relations + Re-fully Define."
- **Best practices to avoid circular references:**
  - Avoid daisy chaining.
  - Hang external references on "key components" and ensure those key components do not depend on external references themselves.
  - Avoid cross-level relationships (top-level assembly $\leftrightarrow$ subassembly components).
  - Avoid adding new external references to features that already have them.
  - Exercise caution with external references in assembly-level features (hole wizard, patterns, assembly cuts, etc.).

---

## 6) Troubleshooting Broken References / Missing Files

- **Find References:** Use `File > Find References...` first to see which file is missing and what its expected path is.
- **Do not save immediately:** For reference repair operations, often it is better to redirect paths using `References...` upon opening, confirm everything is correct, and then save.
- **Replacement rules:** Parts can only be replaced by parts, and subassemblies can only be replaced by subassemblies.

---

## 7) MCP Automated Modeling (Repository Usage Experience Additions)

- **Clear Selection before every selection action:** Reduces `InsertSketch` failures or incorrect host issues.
- **Sketches must be hosted on solid faces first:** Select a flat face on a real solid first, then call `InsertSketch`; do not build a sketch "out of thin air" and gamble on which plane it lands on.
- **Check edit state before reading the tree or deleting:** Call `GetEditState` first; if `IsEditing = true`, call `FinishSketch` first, then run `ListFeatureTree`, `DeleteFeatureByName`, or `DeleteUnusedSketches`.
- **Treat "Exiting Sketch Edit" as part of cleanup:** Tree reading, orphaned sketch cleanup, and deleting features by name should all happen while out of edit mode, never mid-edit.
- **Check cut direction when cutting on a face:** If making a shallow cut from a top face into the solid's interior, you usually need to flip the cut direction into the interior; otherwise, it easily fails.
- **Prioritize modifying non-functional surfaces to fix interferences:** For parts like belt pulley brackets, prioritize trimming top margins or adding clearance slots rather than randomly changing pulley hole locations or diameters.
- **Use `PLANE` as a fallback when using `select_by_name` for reference planes:** `swSelDATUMPLANES` can be unstable in certain environments.
- **Ensure closed contours before Extrude/Cut/Revolve:** Open contours cause features to fail (the bridge layer in this project includes pre-checks that will throw errors directly).
- **Extrude after `FinishSketch` still requires pre-checking:** The current project supports parsing the profile feature from the top layer to perform pre-checks.

---

## 8) Hub / COM Recovery Workflow (Verified in This Repository)

- **Symptom Recognition:** If `get_active_document`, `list_documents`, and `list_components` worked previously but simultaneously start throwing `0x800706BA`, suspect that the Hub has cached an inactive `ISldWorks` COM session.
- **Log Criteria:** If the logs report `RPC server unavailable` on one side while claiming `Connect reused the existing SolidWorks session` on the other, it means it didn't fail to connect—it incorrectly reused a dead connection.
- **Stable Verification Sequence:** After repairing or restarting the Hub, verify using this order: `connect -> get_active_document -> list_documents -> list_components`. Only when this entire chain passes should you proceed with modeling.
- **Stop the old Hub before rebuilding:** If `SolidWorksBridge.dll` is locked by `SolidWorksMcpApp`, kill the old tray process before running `dotnet build`; otherwise, your code fixes won't make it to the running Hub.
- **Current Bridge Layer Strategy:** `Connect()` / `EnsureConnected()` now probes connection activity first; upon encountering a known broken-link HRESULT, it discards the old COM wrapper and re-attaches or creates a new instance.

---

## 9) SolidWorks UI Interaction Philosophy & FeatureTree Key Points

- **The CommandManager is the entry point for "context-switching commands":** It switches tabs based on document type and current workflow stage; always be clear whether you are in a sketch, feature, assembly, or view context.
- **The FeatureManager is not just a display tree; it's an "object locator":** The graphics area and tree are linked. When it's hard to click accurately in the graphics area, prioritize using the tree to locate objects by name, hierarchy, and parent-child relationships.
- **The PropertyManager is the "parameter panel for the current command":** It is suited for changing parameters of the active feature/mate/sketch command, not for understanding overall model structure. Use the FeatureManager for structural understanding.
- **The left-side tree dictates understanding overhead:** Renaming key features, sketches, planes, and components makes subsequent model modifications, interference checks, and parent-child tracing much faster.
- **Parent-child relationships and rebuild order are critical:** The FeatureManager allows you to view Parents/Children and drag features to reorder the rebuild sequence. Evaluate design intent before changing order to avoid breaking a stable model.
- **In assemblies, prioritize hierarchy over visuals:** Visually "seeing a part" in a large assembly does not mean that part is currently active. Always confirm the active document, component name, and component path before making changes.
- **Use split-screen / flyout tree ideas when you need the tree and parameters simultaneously:** The official UI allows the FeatureManager and PropertyManager to coexist. In the MCP workflow, this translates to: "Enumerate/confirm objects first, execute the command, and then return to verify results."
- **Standard items in the tree are worth checking first:** Folders like Reference Planes, Origin, Bodies, Equations, Sensors, and Annotations often expose the root cause of an issue faster than clicking on the model directly.

---

## Reference Sources (For Deeper Exploration)

- https://www.goengineer.com/blog/mirror-2d-sketches-in-solidworks-mirror-entities-and-dynamic-mirror-entites
- https://www.goengineer.com/blog/creating-reference-planes-in-solidworks
- https://www.goengineer.com/blog/solidworks-filletxpert-tool-tutorial
- https://www.goengineer.com/blog/removing-external-references-solidworks-files
- https://www.goengineer.com/blog/managing-external-references-solidworks-assemblies
- https://www.goengineer.com/blog/solidworks-circular-references
- https://www.goengineer.com/blog/repair-broken-references-in-solidworks
- https://help.solidworks.com/2024/english/SolidWorks/sldworks/c_commandmanager.htm
- https://help.solidworks.com/2024/english/SolidWorks/sldworks/c_featuremanager_design_tree_overview.htm