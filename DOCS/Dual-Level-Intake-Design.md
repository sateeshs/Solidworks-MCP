# Dual-Level Intake Design — BIOBUZZ StarterBot

_As of 2026-09-20. Status: **upper roller module assembled** — `Upper Nectar Roller Module.SLDASM` (25 components, all real goBILDA parts, no custom geometry). Positioning against the real chassis is the remaining work (see Next Steps)._

## Problem statement

The stock goBILDA BIOBUZZ StarterBot (`3200-2627-0003`) intake handles **Pollen only**. Confirmed from the official 37-page assembly manual: a single 264mm roller shaft carrying 16× compliant rubber rollers (`3618-4008-0016`, 16mm OD, 30A durometer), chain-driven off one 50.9:1 Yellow Jacket motor. Nectar (91.44mm, 41g) is 29% larger in diameter and 65% heavier than Pollen (71.12mm, 25g) — too big for this mechanism to grip via the same rolling contact.

An earlier concept (**A1: nip-for-Pollen + scoop-for-Nectar**, a static ramp added beside the existing roller) was built in CAD but abandoned as the primary direction — see "Superseded approach" below.

## Current design direction: dual-level intake

Two separate roller intakes stacked at different heights, each properly sized for its own game element, both chain-driven and spinning simultaneously (likely off a shared drivetrain run, similar to the stock single-roller setup):

- **Lower level** — aligned to Pollen (71.12mm / 2.8in)
- **Upper level** — aligned to Nectar (91.44mm / 3.6in)

This avoids the core physics problem that killed the single-roller approach: instead of one mechanism trying to grip two very different ball sizes, each roller only ever needs to handle one known size.

## FTC size constraints (verified against the official 2026-2027 Competition Manual, Section 12)

- **R102 — Starting Configuration:** robot must fit within an **18in × 18in × 18in cube** (45.70cm) at match start. This is a cube, not just a footprint — height counts too.
- **R105 — Expansion Limit:** after the match starts, the robot may expand but must stay within **18in × 24in × 29in tall**.
- **R104:** no weight limit.

## Feasibility check against real measurements

| Quantity | Value | Source |
| --- | --- | --- |
| StarterBot current envelope | 426 × 454 × 329mm (16.77" × 17.87" × 12.95") | Measured live via `IComponent2.GetBox` on the actual CAD |
| Starting-cube limit (each axis) | 457.2mm (18") | R102 |
| Remaining height headroom (estimate) | ~128mm (~5") | 457.2 − 329 |
| Nectar diameter | 91.44mm (3.6") | Official AndyMark spec, confirmed via real CAD (91.95mm actual) |
| Pollen diameter | 71.12mm (2.8") | Official AndyMark spec, confirmed via real CAD (71.12mm exact) |
| **Combined robot height, module actually attached** | **416.2mm (416.2 of 457.2mm limit — 41mm to spare)** | **Measured live via `IComponent2.GetBox` after inserting and correctly orienting the real module — see "Attached to StarterBot" below** |

**Read:** a second, higher intake level needs roughly 100–150mm of vertical clearance (ball diameter + roller/passage mechanism). Against ~128mm of remaining headroom within the starting cube, this is **tight but plausible without relying on the match-start expansion allowance at all** — i.e., potentially fits in the fixed starting configuration, which is simpler than a deployable/expanding mechanism.

## Decisions (resolved)

1. **Stacked directly above the existing roller**, same facing direction — the existing Pollen intake is untouched; the Nectar roller is a second copy of the same mechanism mounted higher on the frame.
2. **Shared drive, both rollers spin together.** No second motor. The new upper roller gets its own 10-tooth sprocket (`3307-4008-0010`, same bore as everything else); a chain loop connects it to the existing roller's sprocket so both spin off the single 50.9:1 Yellow Jacket motor already in the stock build.
3. **Reuse the same roller part for both levels** (`3618-4008-0016`). Roller diameter isn't what determines grip on a given ball size — shaft height/spacing is — so there's no reason to source a different roller for Nectar; using the identical part keeps this build 100% within the "existing goBILDA STEP files only" constraint.

## Complete Bill of Materials

All SKUs below are **confirmed from the actual official 2026-2027 StarterBot w/ Mecanum Wheels assembly manual** (Steps 5–7, pages 4–5) — not estimated. Quantities are for the **new upper roller module only** (the existing lower roller keeps its own stock hardware, untouched).

| # | Part | SKU | Qty | Source / status |
| --- | --- | --- | --- | --- |
| 1 | Intake Roller | `3618-4008-0016` | 16 | ✅ In assembly — `3618-4008-0016 (Intake Roller).SLDPRT` |
| 2 | 264mm Length, 8mm REX Shaft | `2106-4008-2640` | 1 | ✅ In assembly — `2106-4008-2640 (264mm 8mm REX Shaft).SLDPRT` |
| 3 | Dual Block Mount | `1205-0001-0005` | 2 | ✅ In assembly — `1205-0001-0005 (Dual Block Mount).SLDPRT` |
| 4 | 24mm Length, 8mm REX Standoff | `1516-4008-0240` | 1 | ✅ In assembly — `1516-4008-0240 (24mm 8mm REX Standoff).SLDPRT` |
| 5 | 15-Hole U-Channel | `1120-0015-0384` | 1 | ✅ In assembly — `1120-0015-0384 (15-Hole U-Channel).SLDPRT` |
| 6 | 10-Hole Low U-Channel | `1121-0010-0264` | 2 | ✅ In assembly — `1121-0010-0264 (10-Hole Low U-Channel).SLDPRT` (×2 instances) |
| 7 | Set-Screw Sprocket, 8mm REX bore, 10T | `3307-4008-0010` | 1 (new, for the upper shaft) | ✅ In assembly — `3307-4008-0010 (10T Sprocket).SLDPRT` |
| 8 | Chain, steel, 1m length (cut to real spacing once positioned) | `3308-0008-1000` | 1 loop, length TBD | ✅ Part in assembly (placeholder length/position) — `3308-0008-1000 (Steel Chain 1m).SLDPRT`; real cut length still depends on the real vertical spacing (see Next Steps) |
| — | Generic hardware (8mm/12mm/10mm Socket Head Screws) | — | ~6 | Not yet added — standard stock, not SKU-tracked in the manual excerpt |

**All 8 real parts are now assembled** in `Downloads\FTC\Upper Nectar Roller Module.SLDASM` (25 components total: shaft + 16 rollers spaced at the correct 16mm pitch matching the official 264mm shaft spec, 2 Dual Block Mounts, 1 standoff, 1 15-Hole U-Channel, 2 10-Hole Low U-Channels, 1 sprocket, 1 chain). Component positions are geometrically accurate for the roller/shaft spacing (matches the real spec exactly); the mounting-hardware and U-Channel positions are illustrative placeholders, not yet mated — see tooling limitation below.

Also required, generic bearings/washers/shims included with the Hub-Shaft/Dual Block Mount parts per the manual — not separately tracked or added yet.

## Attached to the StarterBot assembly

`Upper Nectar Roller Module-1` is now inserted as a real sub-assembly component inside `3200-2627-0003 - Test Fit A1 Intake.SLDASM`, alongside the StarterBot, the A1 ramp, and the real Pollen/Nectar spheres — not a separate untouched file.

**Two real orientation bugs found and fixed along the way** (worth remembering for any future component placement in this project):

1. **`AddComponent5` never applies rotation** — it only takes an X/Y/Z position, so every part lands at its own as-authored orientation. The 15-Hole U-Channel, 10-Hole Low U-Channels, and the main shaft were all authored with their long axis along their own local **Y**, not X — so despite being positioned correctly along X, they were physically running the wrong way (one U-Channel alone made the module's bounding box 384mm in the wrong axis). Fixed by writing a corrected rotation matrix directly to `IComponent2.Transform2.ArrayData` (a 16-element flat array: 3×3 rotation + XYZ translation + scale) — `AddMate5`/`CreateTransform` are both confirmed broken in this COM environment, but reading and overwriting `ArrayData` on the transform object returned by `Transform2` works.
2. **Wrong stacking axis.** The StarterBot's own measured axes are X=width (426mm), Y=depth (454mm), Z=height (329mm) — but the module was first stacked by increasing **Y**, not Z, putting it in the depth direction instead of up. Fixed with a second `Transform2` rotation (90° about X) remapping the module's local axes onto the chassis's real X/Y/Z, then translated into place.

**Verified result:** module now sits at Z[280.6, 359.4]mm, cleanly above the chassis top (272.4mm) with an ~8mm gap. Combined robot height (chassis bottom to module top): **416.2mm — inside the 457.2mm (18") starting-cube limit with 41mm to spare.** This is a measured result from the real assembled geometry, not the earlier ~128mm headroom estimate.

**Update — drive gear aligned to the real Pollen gear (2026-09-20):** the user selected the Pollen intake's actual driving gear in SolidWorks, which resolved to real parts inside the fused StarterBot: **`2302-0014-0100`** (100-tooth gear, ~110mm dia.) on a **`2106-4008-0800`** (80mm 8mm REX shaft), secured by a **`2920-0001-4008`** collar — real global position (X=125, Y=-172.1, Z=90.8)mm, read via `SelectionManager.GetSelectedObjectsComponent4()` on the user's selection (see the breakthrough technique in memory).

The Nectar module's drive assembly was rebuilt to match: the same 3 real parts (gear/shaft/collar) were added to the module and positioned **perfectly coaxial above the real Pollen gear** (same X=125, Y=-172.1, only Z differs) at Z=196.7mm — ~106mm above the Pollen gear with clean clearance (no overlap; the two ~85-110mm gears would have physically clashed at the first attempted position, 34mm apart center-to-center against a combined radius of 96mm — caught and fixed before finalizing). Verified whole-assembly envelope after this change: **X=426.0, Y=454.2, Z=392.4mm — all within the 457.2mm (18″) limit.**

Still not done: an actual chain (or shaft coupling) physically connecting the two coaxial gears so they truly spin together — they're correctly positioned relative to each other but not yet linked. The `3308-0008-1000` chain part already sits in the module as a placeholder, not yet routed between the two real gear positions.

## Known tooling limitation (affects verification, not the design itself)

This project's SolidWorks MCP automation layer cannot currently extract 3D positions of internal features/bodies (like the existing roller) from the fused StarterBot CAD import — confirmed across every reasonable COM method tried (`GetBox`, `GetMassProperties`, `Transform`, `GetSpecificFeature2`, `CreateMeasure`, `GetFeature` all fail identically). This means any CAD work on this design will need either:
- Manual positioning/mating in the SolidWorks UI (visual placement), or
- The user providing approximate coordinates read directly off the model themselves.

Full technical details logged in memory (`simulation_com_investigation.md` covers the related Simulation COM gap; the roller-position COM limitation itself is logged in `biobuzz_intake_redesign.md`).

## Superseded approach: A1 (single roller + scoop ramp)

Built but not carried forward as the primary direction:
- `Nectar Scoop Ramp - A1 Intake.SLDPRT` — a static wedge ramp (180mm run × 100mm back-wall height × 240mm wide) with 4× M4 mounting holes, meant to shovel Nectar past the existing Pollen-only roller via robot momentum rather than roller contact.
- Test-fit assembly `3200-2627-0003 - Test Fit A1 Intake.SLDASM` — contains the ramp plus real official Pollen/Nectar geometry (extracted from AndyMark's actual field CAD, `am-5850 BIOBUZZ`), but never mated to the chassis (same COM positioning limitation as above) and flagged with a tight ~8mm clearance margin on the back wall.
- Kept on disk as reference / fallback if the dual-level concept proves infeasible, but not the current design direction.

## Next steps (remaining)

Done: all 8 real parts sourced, saved as native SLDPRT, and assembled into `Upper Nectar Roller Module.SLDASM` (25 components) with correct roller/shaft spacing.

1. Add real mates within the module (currently components are precisely *positioned* but not *mated* — shaft-to-U-Channel bearing fits, roller-to-shaft concentricity, sprocket-to-shaft, etc.).
2. **Manually position** the assembled module above the existing roller in the main StarterBot assembly (this step can't be automated — see tooling limitation above). Record the real vertical spacing once placed.
3. Cut the chain to the real spacing found in step 2 and close the loop connecting both sprockets (the chain part currently in the module is a placeholder length/position).
4. Add the generic mounting hardware (Socket Head Screws) called out in the manual but not yet modeled.
5. Re-run the real-geometry test-fit (`Pollen (Official am-5851).SLDPRT`, `Nectar (Official am-5852).SLDPRT` are already built) against the new dual-roller layout to confirm clearance.
6. Confirm total robot height stays under 457.2mm (18") — the ~128mm headroom budget established above.
7. If available, verify dynamically via a manually-built SolidWorks Motion Study (scripted Simulation is blocked — see `simulation_com_investigation.md`).

---

_Mirrors the "Intake redesign" section of the [FTC-2026-2027 Claude Doc](https://claude.ai/artifact/5BJUAWgA9ejK8ZifmL9Cmt) — that version stays live-editable; this is the version-controlled copy in the repo._
