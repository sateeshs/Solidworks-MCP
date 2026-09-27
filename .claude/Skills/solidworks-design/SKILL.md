---
name: solidworks-design
description: Guided workflows for building and inspecting SolidWorks parts/assemblies through this repo's MCP tools (mcp__solidworks__*) — new part/assembly creation, sketch-to-feature checklists, assembly inspection, and known COM dispatch quirks in this codebase. Use whenever the user wants to model, modify, or inspect something in SolidWorks via MCP rather than by hand.
---

# SolidWorks Design (MCP-backed)

This skill orchestrates the `mcp__solidworks__*` tools defined in `solidworks_mcp/server.py`
(this repo's MCP server, driving SolidWorks over win32com/COM). It does not replace those
tools — it sequences them correctly and documents the gotchas specific to this codebase.

For general SolidWorks modeling best practices (sketch stability, mirroring, reference
planes, fillet ordering, external references, feature-tree hygiene), read
`.claude/Skills/solidworks_modeling_skill_notes.md` first — that file is the durable
knowledge base and is not duplicated here.

## Always start here

```
mcp__solidworks__connect_solidworks   # launches SW if not running, or attaches to it
```

Then confirm state before modeling:

```
mcp__solidworks__get_document_info    # what's active right now
mcp__solidworks__get_sketch_status    # is a sketch already open? avoid double-InsertSketch
```

`get_document_info` and `list_open_documents` currently throw COM errors on this project's
binding (see **Known bugs** below) — if either errors out, fall back to the
`execute_python` pattern documented there instead of assuming no document is open.

## Workflow: new part

1. `create_new_part`
2. `create_sketch` with `plane` = Front/Top/Right
3. Draw geometry on that sketch: `draw_rectangle` / `draw_circle` / `draw_line` / `draw_arc` / `draw_polygon`
   (all take `unit`; default is whatever `set_units` last configured — set it explicitly with
   `set_units` first if the user gives dimensions in a specific unit)
4. `close_sketch` — **required** before extrude/cut if the sketch is still open (check via
   `get_sketch_status` if unsure)
5. `extrude_sketch` (depth, optional `both_directions`) or `cut_extrude` (depth/`through_all`/`both_directions`)
6. Optional cleanup features: `fillet_edges` / `chamfer_edges` — do these **last**, after the
   main solid is stable (see notes file §4) — SolidWorks must already have an edge selection
   for these to apply to; select edges via `execute_python` (SelectByID2 or similar) beforehand
   if the caller hasn't already selected something in the UI
7. `list_features` to confirm the tree looks right
8. `save_document` with an explicit `filepath` (don't rely on save-in-place unless the part
   was already opened from disk)

## Workflow: new assembly

1. `create_new_assembly`
2. Insert/position components — **no dedicated MCP tool exists for this yet**; use
   `execute_python` against `doc.AddComponent5(...)` or drag-and-drop is required manually.
   Flag this gap to the user rather than guessing at an insert-component tool that isn't there.
3. `save_document`

## Workflow: inspect an existing assembly/part

`list_features` only works reliably on parts. For assemblies, `doc.FirstFeature` throws
"Member not found" on this COM binding — use `execute_python` and walk components instead:

```python
comps = []
for c in doc.GetComponents(True):
    name = c.Name2 if not callable(c.Name2) else c.Name2()
    supp = c.IsSuppressed() if callable(c.IsSuppressed) else c.IsSuppressed
    comps.append((name, "suppressed" if supp else "active"))
print(comps)
```

This is the pattern validated against this repo's live SolidWorks session — reuse it rather
than re-deriving the property/method dance each time.

## Known bugs in this repo (as of 2026-09-19)

`solidworks_mcp/automation/documents.py` has two confirmed COM-dispatch bugs on the
`win32com.client.dynamic.Dispatch` binding this project ends up using:

- **`get_document_info()`** (line ~342): calls `doc.GetType()` unconditionally. On this
  binding, parameterless COM methods sometimes auto-resolve to their return value on plain
  attribute access, so `doc.GetType` is already an `int` and `()` then fails with
  `'int' object is not callable`. Every other method in the same file guards this with
  `if callable(x): x = x()` — `get_document_info` and `list_open_documents` are the two
  exceptions that don't, and both throw.
- **`list_open_documents()`**: `self._sw_app.GetFirstDocument` raises
  `(-2147352573, 'Member not found.', None, None)` on this SolidWorks/COM binding even
  through the callable-guard pattern — the member itself isn't resolving, not just the
  call style. Root cause not yet fixed; treat this tool as broken until it is.

**Workaround:** when either tool errors, drop to `execute_python` and query `sw`/`doc`
directly using the guarded property pattern shown above, rather than reporting "no document
open" — a document is very likely open and the wrapper is just failing to read it.

If asked to fix these, the fix is: apply the same `if callable(x): x = x()` guard used
elsewhere in `documents.py` to every property access in `get_document_info`, and
investigate why `GetFirstDocument` specifically isn't a resolvable member (possibly needs
`sw.IGetFirstDocument` naming, or a different dispatch path than `GetObject`/`Dispatch`
depending on which of the four connection methods in `automation/base.py` succeeded).

## Units

Call `set_units` once per session/document before drawing if the user gives dimensions in
something other than the current default — every draw/extrude tool accepts a per-call
`unit` override too, so it's safe to mix as long as each call is explicit.
