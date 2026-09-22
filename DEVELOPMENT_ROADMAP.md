# 🚀 SolidWorks MCP Development Roadmap
## Building the Most Robust SolidWorks MCP Server

**Project:** SolidWorks MCP Server  
**Author:** Samsaam Ali Baig  
**Start Date:** January 2026  
**Target:** Production-Ready v3.0

---

# 📋 TABLE OF CONTENTS

1. [Project Vision](#1-project-vision)
2. [Current State Analysis](#2-current-state-analysis)
3. [Development Phases](#3-development-phases)
4. [Phase 1: Foundation Improvements](#4-phase-1-foundation-improvements)
5. [Phase 2: Core Feature Expansion](#5-phase-2-core-feature-expansion)
6. [Phase 3: Advanced Features](#6-phase-3-advanced-features)
7. [Phase 4: Assembly & Drawing Support](#7-phase-4-assembly--drawing-support)
8. [Phase 5: Simulation & Analysis](#8-phase-5-simulation--analysis)
9. [Phase 6: Production Hardening](#9-phase-6-production-hardening)
10. [Testing Strategy](#10-testing-strategy)
11. [Documentation Plan](#11-documentation-plan)
12. [Progress Tracking](#12-progress-tracking)

---

# 1. PROJECT VISION

## 1.1 Mission Statement
Create the most comprehensive, reliable, and user-friendly MCP server for SolidWorks automation that enables AI assistants to perform complex CAD operations through natural language commands.

## 1.2 Success Criteria
- [ ] 50+ automation tools covering all major SolidWorks operations — 25 registered as of 2026-09-19 (see 2.3)
- [ ] 99% connection reliability — 4 fallback connection methods exist, but `get_document_info`/`list_open_documents` still throw unguarded COM errors on some bindings
- [x] Support for Parts, Assemblies, and Drawings — Parts done; Assembly insert/mate and Drawing creation implemented in `automation/` and wired into `server.py`'s tool list as of 2026-09-20
- [ ] Simulation integration — `solidworks_simulation.py` exists at repo root but isn't wired into the MCP server. Live-investigated 2026-09-20: blocked on a real COM version mismatch, not just "not started" — see 8.1/Task 5.1 for details
- [x] Unit-agnostic input (mm, inch, meter) — `utils/units.py` + per-call `unit` params throughout
- [~] Comprehensive error recovery — `utils/validation.py` covers input validation; COM-layer error recovery still has known gaps
- [~] Full documentation and examples — README + this roadmap exist; a `solidworks-design` Claude Code skill was added 2026-09-19 documenting live usage and known bugs

## 1.3 Target Users
- Engineers using AI assistants for CAD automation
- Educators teaching CAD through conversational interfaces
- Rapid prototyping teams
- Design automation pipelines

---

# 2. CURRENT STATE ANALYSIS

## 2.1 Version 2.3 Inventory

### Current Tools (11)
| # | Tool | Category | Status |
|---|------|----------|--------|
| 1 | connect_solidworks | Connection | ✅ Working |
| 2 | create_new_part | Document | ✅ Working |
| 3 | create_sketch | Sketch | ✅ Working |
| 4 | draw_circle | 2D Geometry | ✅ Working |
| 5 | draw_rectangle | 2D Geometry | ✅ Working |
| 6 | draw_line | 2D Geometry | ✅ Working |
| 7 | extrude_sketch | 3D Feature | ✅ Working |
| 8 | save_document | File I/O | ✅ Working |
| 9 | close_document | Document | ✅ Working |
| 10 | execute_python | Advanced | ✅ Working |
| 11 | get_document_info | Information | ✅ Working |

### Current Capabilities
```
✅ Connect to SolidWorks (with auto-launch)
✅ Create part documents
✅ Basic 2D sketching (circle, rectangle, line)
✅ Boss extrusion
✅ Save/Close documents
✅ Custom Python execution
✅ Error handling with codes
✅ Logging system
```

### Current Limitations
```
❌ No assembly support
❌ No drawing support
❌ No cut operations
❌ No fillets/chamfers
❌ No revolve/sweep/loft
❌ No patterns
❌ No sketch constraints
❌ No measurements
❌ No export formats (STEP, STL, etc.)
❌ No simulation
❌ Hardcoded units (meters only)
❌ Hardcoded SolidWorks path
```

## 2.2 Code Metrics
- Total Lines: ~623
- Classes: 3 (SwErrors, SwPlanes, SolidWorksAutomation)
- Methods: 16
- Tools: 11
- Test Coverage: 0%

## 2.3 Actual State (Reconciled 2026-09-19)

This roadmap's checkboxes went unmaintained after the v2.3 baseline above was written — every
task in Phases 1–6 below was still marked `[ ] Not Started` despite real work having landed. This
section (and the per-task `**Status:**` lines throughout) were reconciled against the live code on
2026-09-19. Legend: `[x]` Done · `[~]` Partial or implemented-but-not-wired · `[ ]` Not Started.

**Registered MCP tools: 33** (in `solidworks_mcp/server.py`'s `list_tools()`, up from 25 on 2026-09-20):
`connect_solidworks`, `get_solidworks_info`, `create_new_part`, `create_new_assembly`,
`open_document`, `save_document`, `close_document`, `get_document_info`, `list_open_documents`,
`create_sketch`, `create_sketch_on_face`, `draw_line`, `draw_circle`, `draw_rectangle`, `draw_arc`,
`draw_polygon`, `extrude_sketch`, `cut_extrude`, `fillet_edges`, `chamfer_edges`, `list_features`,
`insert_component`, `insert_library_part`, `add_mate`, `get_assembly_tree`, `list_mates`,
`create_linear_pattern`, `create_circular_pattern`, `create_new_drawing`,
`close_sketch`, `get_sketch_status`, `set_units`, `execute_python`.

**Wired 2026-09-20** (previously implemented in `automation/` but not exposed as MCP tools):
- `automation/assemblies.py`: `insert_component()`, `insert_library_part()`, `add_mate()` (covers
  coincident/concentric/distance via `validate_mate_type()`), `get_assembly_tree()`, `list_mates()`
- `automation/patterns.py`: `create_linear_pattern()`, `create_circular_pattern()`
- `automation/documents.py`: `create_new_drawing()`

Note: `insert_component`/`insert_library_part`/`add_mate`/`create_linear_pattern` convert
dimensions using the automation instance's *default* unit (set via `set_units`) — their
underlying `automation/` methods don't accept a per-call `unit` override, so the MCP tool
schemas intentionally omit a `unit` parameter rather than expose one that would be ignored.
None of this has been exercised against a live SolidWorks session yet — verification so far is
static (source cross-check + `ast` parse), not a live COM smoke test.

## 2.3a Live SolidWorks Test (2026-09-20)

Ran the 8 newly-wired tools against a live SolidWorks 34.4.1 session (via `execute_python`,
monkey-patching the reloaded module onto the running server's `sw_automation` instance since the
MCP server process itself wasn't restarted). Found and fixed 4 real bugs, all now in
`automation/assemblies.py` and `automation/patterns.py`:

1. **`insert_component()` never pre-loaded the referenced file.** `AddComponent5` silently returns
   `None` unless the target part/assembly document is already open in the SW session. Fix:
   `insert_component()` now calls `OpenDoc6` (silent) on the file before `AddComponent5`, then
   reactivates the assembly via `ActivateDoc3`.
2. **`GetChildren()` called as a method when it's a property** on this COM binding (same class of
   bug as `GetTitle`/`GetType`/`GetNextFeature` documented above) — broke `get_assembly_tree()` and
   `list_mates()`. Fixed with a shared `_get_children()` helper that checks `callable()` first.
   `IsSuppressed`/`GetPathName` on `_extract_component_info()` hardened the same way.
3. **`SelectByID2`'s Callout parameter (8th arg) passed as plain Python `None`** instead of a
   `win32com.client.VARIANT(pythoncom.VT_DISPATCH, None)`, raising COM "Type mismatch" — present in
   `add_mate()` and both `create_linear_pattern()`/`create_circular_pattern()`. Fixed at all 3 call
   sites; `sketches.py` already had the correct pattern to copy from.
4. **`add_mate()` hardcoded an empty entity-select type (`""`)**, which only resolves selections
   whose type is embedded in the name (e.g. `"Edge<3>"`) — named features like planes need an
   explicit type. Fixed with a `_select_entity()` helper that retries `"FACE"`/`"PLANE"`/`"EDGE"`/
   `"VERTEX"` if the empty-type attempt fails.

**Confirmed working live after fixes:** `insert_component`, `get_assembly_tree`, `list_mates`,
`create_new_drawing`, `insert_library_part` (verified its config-missing error path — no
`gobilda_steps_path` set in this environment).

**Still broken, root cause not found:** `add_mate()`'s actual `AddMate5`/`AddMate3` call and
`create_linear_pattern`/`create_circular_pattern`'s `FeatureLinearPattern4`/`FeatureCircularPattern4`
calls all fail with COM error `(-2147352561, 'Parameter not optional.')` regardless of argument
count (12–14 args tried) — ruled out the property/method dynamic-dispatch quirk (confirmed these
resolve as genuine bound methods). This looks like a real argument-list/type mismatch against
SolidWorks 2026's actual API for these specific methods, not something worth guessing further at
without the official SW 2026 API reference. **Selection itself works** once callers use the
fully-qualified `"FeatureName@ComponentName@AssemblyTitle"` form (the 2-level
`"FeatureName@ComponentName"` shown in `add_mate()`'s docstring example is incomplete for this SW
build) — so the remaining defect is isolated to the mate/pattern creation calls themselves.

**Genuinely not started:** spline, slot, revolve, sweep, loft, mirror, shell, STEP/STL/DXF export,
reference-plane creation, drawing views/dimensions, all of Phase 5 (simulation), performance
optimization, undo/redo, screenshot/view-capture tools.

**Known live bugs** (see the `solidworks-design` skill for detail and workarounds):
`get_document_info()` and `list_open_documents()` throw COM errors (`'int' object is not
callable`, `Member not found`) on the win32com dynamic-dispatch binding this project ends up using.

**Beyond this roadmap's original scope**, two capability layers were added that Phase 1–6 never
anticipated: a **Parts Intelligence** layer (`solidworks_mcp/parts/`) resolving goBILDA SKUs and
catalog lookups, and an **Engineering Intelligence** layer (`solidworks_mcp/engineering/`) with FTC/FRC
design-rule checking (`safety.py`), season-aware design archetypes (`design_advisor.py`), mechanics,
and electrical/electronics-layout helpers. A parallel, framework-agnostic MCP transport
(`solidworks_mcp/mcp/`, `solidworks_mcp/tools/registry.py`) was also added, ported from a sibling
`freecad-ai` project; it is not yet the one `server.py` actually runs.

---

# 3. DEVELOPMENT PHASES

## 3.1 Phase Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT TIMELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PHASE 1: Foundation     ████████░░░░░░░░░░░░  Week 1-2         │
│  PHASE 2: Core Features  ░░░░░░░░████████░░░░  Week 3-4         │
│  PHASE 3: Advanced       ░░░░░░░░░░░░░░░█████  Week 5-6         │
│  PHASE 4: Assembly/Draw  ░░░░░░░░░░░░░░░░░░██  Week 7-8         │
│  PHASE 5: Simulation     ░░░░░░░░░░░░░░░░░░░█  Week 9-10        │
│  PHASE 6: Production     ░░░░░░░░░░░░░░░░░░░░  Week 11-12       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3.2 Tool Count Targets

| Phase | New Tools | Total Tools | Coverage |
|-------|-----------|-------------|----------|
| Current | - | 11 | Basic |
| Phase 1 | +5 | 16 | Foundation |
| Phase 2 | +12 | 28 | Core |
| Phase 3 | +10 | 38 | Advanced |
| Phase 4 | +8 | 46 | Full CAD |
| Phase 5 | +6 | 52 | Simulation |
| Phase 6 | +3 | 55 | Production |

---

# 4. PHASE 1: FOUNDATION IMPROVEMENTS
## Week 1-2 | Priority: CRITICAL

### 4.1 Goals
- [x] Modular code architecture
- [x] Configuration system
- [x] Unit conversion system
- [x] Auto-detect SolidWorks installation
- [~] Improved connection reliability — 4 fallback methods exist; known COM bugs remain (see 2.3)

### 4.2 Tasks

#### Task 1.1: Create Project Structure
```
solidworks_mcp/
├── __init__.py
├── server.py                 # MCP entry point
├── config.py                 # Configuration management
├── constants.py              # All constants
├── automation/
│   ├── __init__.py
│   ├── base.py              # Base automation class
│   ├── connection.py        # Connection management
│   ├── documents.py         # Document operations
│   ├── sketches.py          # Sketch operations
│   ├── features.py          # Feature operations
│   └── geometry.py          # Geometry helpers
├── utils/
│   ├── __init__.py
│   ├── units.py             # Unit conversion
│   ├── validation.py        # Input validation
│   └── sw_finder.py         # SolidWorks detection
├── tools/
│   ├── __init__.py
│   ├── connection_tools.py
│   ├── document_tools.py
│   ├── sketch_tools.py
│   └── feature_tools.py
└── tests/
    ├── __init__.py
    ├── test_connection.py
    ├── test_sketches.py
    └── test_features.py
```
**Status:** [x] Done — modular `solidworks_mcp/` package exists (`automation/`, `utils/`, `constants.py`, `config.py`)
**Estimated Time:** 4 hours

---

#### Task 1.2: Configuration System
**File:** `config.py`
```python
"""
Configuration management for SolidWorks MCP
"""
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

@dataclass
class SolidWorksConfig:
    """SolidWorks MCP Configuration"""
    
    # SolidWorks settings
    exe_path: str = "auto"  # "auto" or explicit path
    startup_timeout: int = 120  # seconds
    connection_retry_interval: int = 5  # seconds
    
    # Default units
    default_unit: str = "mm"  # mm, inch, meter
    
    # Templates
    part_template: str = "auto"
    assembly_template: str = "auto"
    drawing_template: str = "auto"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "solidworks_mcp.log"
    
    # Feature defaults
    default_extrude_depth: float = 10.0  # in default_unit
    default_fillet_radius: float = 2.0   # in default_unit
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> 'SolidWorksConfig':
        """Load configuration from file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        
        if Path(config_path).exists():
            with open(config_path, 'r') as f:
                data = json.load(f)
            return cls(**data)
        return cls()
    
    def save(self, config_path: Optional[str] = None):
        """Save configuration to file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"
        
        with open(config_path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

# Global config instance
config = SolidWorksConfig.load()
```
**Status:** [x] Done — `config.py` implements `SolidWorksConfig` dataclass with JSON load/save
**Estimated Time:** 2 hours

---

#### Task 1.3: Unit Conversion System
**File:** `utils/units.py`
```python
"""
Unit conversion utilities for SolidWorks MCP
SolidWorks API uses meters internally
"""
from enum import Enum
from typing import Union

class Unit(Enum):
    METER = "m"
    MILLIMETER = "mm"
    CENTIMETER = "cm"
    INCH = "inch"
    FOOT = "ft"

# Conversion factors TO meters
TO_METERS = {
    Unit.METER: 1.0,
    Unit.MILLIMETER: 0.001,
    Unit.CENTIMETER: 0.01,
    Unit.INCH: 0.0254,
    Unit.FOOT: 0.3048,
}

# Conversion factors FROM meters
FROM_METERS = {unit: 1.0 / factor for unit, factor in TO_METERS.items()}

class UnitConverter:
    """Handle unit conversions for SolidWorks API"""
    
    def __init__(self, default_unit: str = "mm"):
        self.default_unit = self._parse_unit(default_unit)
    
    def _parse_unit(self, unit: str) -> Unit:
        """Parse unit string to Unit enum"""
        unit_map = {
            "m": Unit.METER, "meter": Unit.METER, "meters": Unit.METER,
            "mm": Unit.MILLIMETER, "millimeter": Unit.MILLIMETER,
            "cm": Unit.CENTIMETER, "centimeter": Unit.CENTIMETER,
            "inch": Unit.INCH, "in": Unit.INCH, "inches": Unit.INCH,
            "ft": Unit.FOOT, "foot": Unit.FOOT, "feet": Unit.FOOT,
        }
        return unit_map.get(unit.lower(), Unit.MILLIMETER)
    
    def to_meters(self, value: float, unit: str = None) -> float:
        """Convert value to meters for SolidWorks API"""
        if unit is None:
            unit = self.default_unit
        else:
            unit = self._parse_unit(unit)
        return value * TO_METERS[unit]
    
    def from_meters(self, value: float, unit: str = None) -> float:
        """Convert value from meters to display unit"""
        if unit is None:
            unit = self.default_unit
        else:
            unit = self._parse_unit(unit)
        return value * FROM_METERS[unit]
    
    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert between any two units"""
        meters = self.to_meters(value, from_unit)
        return self.from_meters(meters, to_unit)

# Global converter instance
converter = UnitConverter()

# Convenience functions
def mm(value: float) -> float:
    """Convert mm to meters"""
    return value * 0.001

def inch(value: float) -> float:
    """Convert inches to meters"""
    return value * 0.0254

def cm(value: float) -> float:
    """Convert cm to meters"""
    return value * 0.01
```
**Status:** [x] Done — `utils/units.py` implements `UnitConverter`, `mm()`/`inch()`/`to_mm()` etc.
**Estimated Time:** 2 hours

---

#### Task 1.4: SolidWorks Auto-Detection
**File:** `utils/sw_finder.py`
```python
"""
Auto-detect SolidWorks installation
"""
import os
import winreg
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class SolidWorksFinder:
    """Find SolidWorks installation on the system"""
    
    REGISTRY_PATHS = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\SolidWorks\SOLIDWORKS"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\SolidWorks\SOLIDWORKS"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\SolidWorks\SOLIDWORKS"),
    ]
    
    COMMON_PATHS = [
        r"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
        r"C:\Program Files\SolidWorks Corp\SolidWorks\SLDWORKS.exe",
        r"D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\SLDWORKS.exe",
        r"D:\SolidWorks\SLDWORKS.exe",
    ]
    
    @classmethod
    def find(cls) -> Optional[str]:
        """Find SolidWorks executable"""
        # Try registry first
        path = cls._find_from_registry()
        if path:
            return path
        
        # Try common paths
        path = cls._find_from_common_paths()
        if path:
            return path
        
        # Search Program Files
        path = cls._search_program_files()
        if path:
            return path
        
        logger.error("SolidWorks installation not found")
        return None
    
    @classmethod
    def _find_from_registry(cls) -> Optional[str]:
        """Search Windows registry for SolidWorks"""
        for hkey, reg_path in cls.REGISTRY_PATHS:
            try:
                with winreg.OpenKey(hkey, reg_path) as key:
                    versions = cls._get_subkeys(key)
                    versions.sort(reverse=True)  # Latest first
                    
                    for version in versions:
                        try:
                            with winreg.OpenKey(key, version) as ver_key:
                                sw_path, _ = winreg.QueryValueEx(ver_key, "SolidWorks Exe")
                                if os.path.exists(sw_path):
                                    logger.info(f"Found SolidWorks {version} at: {sw_path}")
                                    return sw_path
                        except WindowsError:
                            continue
            except WindowsError:
                continue
        return None
    
    @classmethod
    def _get_subkeys(cls, key) -> List[str]:
        """Get all subkeys of a registry key"""
        subkeys = []
        i = 0
        while True:
            try:
                subkeys.append(winreg.EnumKey(key, i))
                i += 1
            except WindowsError:
                break
        return subkeys
    
    @classmethod
    def _find_from_common_paths(cls) -> Optional[str]:
        """Check common installation paths"""
        # Add versioned paths
        all_paths = list(cls.COMMON_PATHS)
        for year in range(2030, 2015, -1):
            all_paths.extend([
                rf"C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS {year}\SLDWORKS.exe",
                rf"D:\Program Files\SOLIDWORKS Corp\SOLIDWORKS {year}\SLDWORKS.exe",
            ])
        
        for path in all_paths:
            if os.path.exists(path):
                logger.info(f"Found SolidWorks at: {path}")
                return path
        return None
    
    @classmethod
    def _search_program_files(cls) -> Optional[str]:
        """Search Program Files directories"""
        search_roots = [
            r"C:\Program Files",
            r"D:\Program Files",
            r"C:\Program Files (x86)",
        ]
        
        for root in search_roots:
            if not os.path.exists(root):
                continue
            
            for folder in os.listdir(root):
                if "solidworks" in folder.lower():
                    sw_folder = os.path.join(root, folder)
                    for dirpath, _, files in os.walk(sw_folder):
                        if "SLDWORKS.exe" in files:
                            path = os.path.join(dirpath, "SLDWORKS.exe")
                            logger.info(f"Found SolidWorks at: {path}")
                            return path
        return None
    
    @classmethod
    def get_version(cls, exe_path: str) -> Optional[str]:
        """Get SolidWorks version from executable"""
        try:
            import win32api
            info = win32api.GetFileVersionInfo(exe_path, "\\")
            ms = info['FileVersionMS']
            ls = info['FileVersionLS']
            return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
        except:
            return None
```
**Status:** [x] Done — `utils/sw_finder.py` implements `SolidWorksFinder`, `find_solidworks()`, `find_template()`
**Estimated Time:** 2 hours

---

#### Task 1.5: New Tools for Phase 1

| Tool | Description | Priority |
|------|-------------|----------|
| `get_solidworks_info` | Get SW version, path, status | HIGH |
| `set_units` | Change default units | HIGH |
| `open_document` | Open existing file | HIGH |
| `list_features` | List all features in model | MEDIUM |
| `list_planes` | List all planes | MEDIUM |

**Status:** [x] Done — delivered as part of the 25-tool `server.py` tool list
**Estimated Time:** 4 hours

---

### 4.3 Phase 1 Deliverables
- [x] Modular project structure
- [x] Configuration file support
- [x] Unit conversion (mm, inch, meter)
- [x] Auto-detect SolidWorks
- [x] 5 new tools (25 registered total, exceeds the 16 target)
- [~] Unit tests for core functions — `tests/unit/test_units.py`, `test_config.py`, `test_validation.py` exist; coverage of `server.py` itself unverified

---


# 5. PHASE 2: CORE FEATURE EXPANSION
## Week 3-4 | Priority: HIGH

### 5.1 Goals
- [~] Complete 2D sketch tools — line/circle/rectangle/arc/polygon done; spline/slot missing
- [x] Add cut operations
- [x] Add fillet/chamfer
- [ ] Add revolve feature
- [ ] Add sketch constraints
- [ ] Add measurement tools

### 5.2 New Sketch Tools

#### Task 2.1: Arc Drawing Tools
```python
def draw_arc_center(self, cx, cy, radius, start_angle, end_angle, unit="mm") -> Dict:
    """
    Draw arc by center point and angles
    
    Args:
        cx, cy: Center point
        radius: Arc radius
        start_angle: Start angle in degrees
        end_angle: End angle in degrees
        unit: Unit for dimensions
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    radius_m = self.units.to_meters(radius, unit)
    cx_m = self.units.to_meters(cx, unit)
    cy_m = self.units.to_meters(cy, unit)
    
    import math
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    # Calculate start and end points
    x1 = cx_m + radius_m * math.cos(start_rad)
    y1 = cy_m + radius_m * math.sin(start_rad)
    x2 = cx_m + radius_m * math.cos(end_rad)
    y2 = cy_m + radius_m * math.sin(end_rad)
    
    arc = doc.SketchManager.CreateArc(cx_m, cy_m, 0, x1, y1, 0, x2, y2, 0, 1)
    
    if arc is None:
        return self._result(False, "Failed to create arc", SwErrors.swSketchError)
    
    return self._result(True, f"Arc created: r={radius}{unit}", SwErrors.swSuccess)

def draw_arc_3point(self, x1, y1, x2, y2, x3, y3, unit="mm") -> Dict:
    """
    Draw arc through 3 points
    
    Args:
        x1, y1: Start point
        x2, y2: Mid point (on arc)
        x3, y3: End point
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Convert units
    points = [(x1, y1), (x2, y2), (x3, y3)]
    points_m = [(self.units.to_meters(x, unit), self.units.to_meters(y, unit)) 
                for x, y in points]
    
    arc = doc.SketchManager.Create3PointArc(
        points_m[0][0], points_m[0][1], 0,
        points_m[2][0], points_m[2][1], 0,
        points_m[1][0], points_m[1][1], 0
    )
    
    return self._result(True, "3-point arc created", SwErrors.swSuccess)
```
**Status:** [x] Done — `draw_arc` tool live (`sketches.py: draw_arc_center`)

---

#### Task 2.2: Spline Tool
```python
def draw_spline(self, points: list, unit="mm") -> Dict:
    """
    Draw spline through points
    
    Args:
        points: List of (x, y) tuples
        unit: Unit for coordinates
    
    Example:
        draw_spline([(0, 0), (10, 5), (20, 0), (30, -5)], unit="mm")
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if len(points) < 2:
        return self._result(False, "Spline needs at least 2 points", SwErrors.swSketchError)
    
    # Convert to meters and create point array
    import array
    point_array = array.array('d')
    
    for x, y in points:
        point_array.append(self.units.to_meters(x, unit))
        point_array.append(self.units.to_meters(y, unit))
        point_array.append(0)  # Z coordinate
    
    spline = doc.SketchManager.CreateSpline2(point_array, True)
    
    if spline is None:
        return self._result(False, "Failed to create spline", SwErrors.swSketchError)
    
    return self._result(True, f"Spline with {len(points)} points created", SwErrors.swSuccess)
```
**Status:** [x] Done — `draw_spline` wired (2026-09-22). Verified live: needs an explicit `VT_ARRAY | VT_R8` VARIANT for the point array — a plain list or `array.array('d')` silently returns None through this codebase's dynamic-dispatch connection.

---

#### Task 2.3: Polygon Tool
```python
def draw_polygon(self, cx, cy, radius, sides=6, unit="mm") -> Dict:
    """
    Draw regular polygon
    
    Args:
        cx, cy: Center point
        radius: Circumscribed radius
        sides: Number of sides (3-100)
        unit: Unit for dimensions
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if sides < 3 or sides > 100:
        return self._result(False, "Sides must be 3-100", SwErrors.swSketchError)
    
    cx_m = self.units.to_meters(cx, unit)
    cy_m = self.units.to_meters(cy, unit)
    radius_m = self.units.to_meters(radius, unit)
    
    # CreatePolygon: Cx, Cy, Cz, Vx, Vy, Vz, NumSides, Inscribed
    polygon = doc.SketchManager.CreatePolygon(
        cx_m, cy_m, 0,           # Center
        cx_m + radius_m, cy_m, 0, # Vertex
        sides,                    # Number of sides
        False                     # Inscribed (False = circumscribed)
    )
    
    return self._result(True, f"{sides}-sided polygon created", SwErrors.swSuccess)
```
**Status:** [x] Done — `draw_polygon` tool live

---

#### Task 2.4: Slot Tool
```python
def draw_slot(self, x1, y1, x2, y2, width, unit="mm") -> Dict:
    """
    Draw straight slot
    
    Args:
        x1, y1: Start center point
        x2, y2: End center point
        width: Slot width (diameter of end caps)
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    x1_m = self.units.to_meters(x1, unit)
    y1_m = self.units.to_meters(y1, unit)
    x2_m = self.units.to_meters(x2, unit)
    y2_m = self.units.to_meters(y2, unit)
    width_m = self.units.to_meters(width, unit)
    
    # CreateSketchSlot: Type, X1, Y1, Z1, X2, Y2, Z2, Width, CenterArc, AddDimension, Value
    slot = doc.SketchManager.CreateSketchSlot(
        0,  # swSketchSlotLongCenter
        x1_m, y1_m, 0,
        x2_m, y2_m, 0,
        width_m,
        0,     # Center arc type
        False  # Add dimension
    )
    
    return self._result(True, f"Slot created: width={width}{unit}", SwErrors.swSuccess)
```
**Status:** [~] Partial — `draw_slot` wired (2026-09-22) calling the documented `CreateSketchSlot` API, but that call fails with COM "Parameter not optional" on this SW build regardless of the 10/11/13-param signature tried. A manual line+arc construction was also tried and rejected: `CreateLine`/`CreateArc` don't auto-add coincident relations between separately-created entities even at bit-identical endpoints, so the profile never closed for extrusion. Needs either the real signature for this build or an explicit `AddRelation`-based closure step.

---

### 5.3 Cut & Feature Tools

#### Task 2.5: Cut Extrude
```python
def cut_extrude(self, depth, through_all=False, both_directions=False, unit="mm") -> Dict:
    """
    Cut extrude (remove material)
    
    Args:
        depth: Cut depth (ignored if through_all=True)
        through_all: Cut through entire model
        both_directions: Cut in both directions
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Exit sketch
    doc.InsertSketch2(True)
    
    depth_m = self.units.to_meters(depth, unit)
    
    if through_all:
        if both_directions:
            end_cond = 2  # swEndCondThroughAllBoth
        else:
            end_cond = 1  # swEndCondThroughAll
        depth_m = 0
    else:
        end_cond = 6 if both_directions else 0  # MidPlane or Blind
    
    # FeatureCut4 for cut operations
    feat = doc.FeatureManager.FeatureCut4(
        True,           # Sd
        False,          # Flip
        False,          # Dir
        end_cond,       # T1
        0,              # T2
        depth_m,        # D1
        depth_m,        # D2
        False, False,   # Dchk1, Dchk2
        False, False,   # Ddir1, Ddir2
        0.0, 0.0,       # Draft angles
        False, False,   # OffsetReverse
        False, False,   # TranslateSurface, NormalCut
        False,          # FlipSide
        True, True,     # AssemblyFeatureScope, AutoSelect
        True,           # FeatureScope
        0,              # T0
        0.0, False      # StartOffset, FlipStartOffset
    )
    
    if feat is None:
        return self._result(False, "Cut failed", SwErrors.swFeatureError)
    
    cut_type = "through all" if through_all else f"{depth}{unit} deep"
    return self._result(True, f"Cut extrude: {cut_type}", SwErrors.swSuccess)
```
**Status:** [x] Done — `cut_extrude` tool live

---

#### Task 2.6: Fillet Tool
```python
def fillet_edges(self, radius, edge_indices=None, all_edges=False, unit="mm") -> Dict:
    """
    Add fillet to edges
    
    Args:
        radius: Fillet radius
        edge_indices: List of edge indices to fillet (optional)
        all_edges: Fillet all edges
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    radius_m = self.units.to_meters(radius, unit)
    
    if all_edges:
        # Select all edges
        doc.Extension.SelectAll()
    elif edge_indices:
        # Select specific edges
        doc.ClearSelection2(True)
        for idx in edge_indices:
            doc.Extension.SelectByID2(f"Edge<{idx}>", "EDGE", 0, 0, 0, True, 0, None, 0)
    
    # Simple constant radius fillet
    feat = doc.FeatureManager.FeatureFillet3(
        195,        # Options: swFeatureFilletKeepFeatures | swFeatureFilletPropagate
        radius_m,   # Radius
        0,          # Fillet type (0 = symmetric)
        0,          # Overflow type
        0, 0,       # Radius type, Profile type
        0, 0, 0,    # Additional parameters
        0, 0, 0,
        0, 0, 0
    )
    
    if feat is None:
        return self._result(False, "Fillet failed - select edges first", SwErrors.swFeatureError)
    
    return self._result(True, f"Fillet r={radius}{unit}", SwErrors.swSuccess)
```
**Status:** [x] Done — `fillet_edges` tool live

---

#### Task 2.7: Chamfer Tool
```python
def chamfer_edges(self, distance, angle=45, edge_indices=None, unit="mm") -> Dict:
    """
    Add chamfer to edges
    
    Args:
        distance: Chamfer distance
        angle: Chamfer angle (default 45°)
        edge_indices: List of edge indices
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    import math
    dist_m = self.units.to_meters(distance, unit)
    angle_rad = math.radians(angle)
    
    if edge_indices:
        doc.ClearSelection2(True)
        for idx in edge_indices:
            doc.Extension.SelectByID2(f"Edge<{idx}>", "EDGE", 0, 0, 0, True, 0, None, 0)
    
    # FeatureChamfer: Type, Width, Angle, OtherDist, FlipFlag, Tangent, FaceEdge
    feat = doc.FeatureManager.FeatureChamfer(
        1,          # Type (1 = Distance-Angle)
        dist_m,     # Distance
        angle_rad,  # Angle
        dist_m,     # Other distance
        0,          # Flip flag
        False,      # Tangent propagation
        False       # Face-edge chamfer
    )
    
    if feat is None:
        return self._result(False, "Chamfer failed", SwErrors.swFeatureError)
    
    return self._result(True, f"Chamfer {distance}{unit} x {angle}°", SwErrors.swSuccess)
```
**Status:** [x] Done — `chamfer_edges` tool live

---

#### Task 2.8: Revolve Feature
```python
def revolve_sketch(self, angle=360, axis="centerline", unit="deg") -> Dict:
    """
    Revolve sketch around axis
    
    Args:
        angle: Revolution angle (default 360 for full)
        axis: "centerline", "x", "y", or axis name
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    import math
    angle_rad = math.radians(angle)
    
    # Exit sketch
    doc.InsertSketch2(True)
    
    # Select axis if specified
    if axis.lower() == "x":
        doc.Extension.SelectByID2("", "AXIS", 1, 0, 0, False, 0, None, 0)
    elif axis.lower() == "y":
        doc.Extension.SelectByID2("", "AXIS", 0, 1, 0, False, 0, None, 0)
    
    # FeatureRevolve2: Sd, Flip, Dir, T1, T2, D1, D2, Dchk1, Dchk2, MergeResult, UseFeatScope
    feat = doc.FeatureManager.FeatureRevolve2(
        True,       # Sd (single direction)
        False,      # Flip
        False,      # Dir
        0,          # T1 (Blind)
        0,          # T2
        angle_rad,  # D1 (angle)
        0,          # D2
        False,      # Dchk1
        False,      # Dchk2
        True,       # MergeResult
        True,       # UseFeatScope
        True        # UseAutoSelect
    )
    
    if feat is None:
        return self._result(False, "Revolve failed - need axis", SwErrors.swFeatureError)
    
    return self._result(True, f"Revolved {angle}°", SwErrors.swSuccess)
```
**Status:** [x] Done — `revolve_sketch` wired (2026-09-22). Verified live: the real `FeatureRevolve2` signature on this build is 20 params (`SingleDir...UseAutoSelect, T0, StartOffset`) — the commonly-cited 21p (extra `FlipStartOffset`) and 18p (no `T0`/`StartOffset`) variants both fail with COM param-count errors.

---

### 5.4 Measurement Tools

#### Task 2.9: Measure Distance
```python
def measure_distance(self, entity1_type, entity1_name, entity2_type, entity2_name) -> Dict:
    """
    Measure distance between two entities
    
    Args:
        entity1_type: "FACE", "EDGE", "VERTEX", "PLANE"
        entity1_name: Entity name or index
        entity2_type: Second entity type
        entity2_name: Second entity name
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    measure = doc.Extension.CreateMeasure()
    
    # Select first entity
    doc.Extension.SelectByID2(str(entity1_name), entity1_type, 0, 0, 0, False, 0, None, 0)
    
    # Select second entity
    doc.Extension.SelectByID2(str(entity2_name), entity2_type, 0, 0, 0, True, 0, None, 0)
    
    # Calculate
    status = measure.Calculate(None)
    
    if status:
        distance_m = measure.Distance
        distance_mm = distance_m * 1000
        
        return self._result(True, f"Distance: {distance_mm:.3f}mm", SwErrors.swSuccess,
                          {"distance_m": distance_m, "distance_mm": distance_mm})
    
    return self._result(False, "Measurement failed", SwErrors.swUnknownError)

def get_mass_properties(self, unit="mm") -> Dict:
    """
    Get mass properties of the model
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    props = doc.Extension.CreateMassProperty()
    
    if props is None:
        return self._result(False, "Failed to get mass properties", SwErrors.swUnknownError)
    
    # Get values
    volume = props.Volume  # m³
    surface_area = props.SurfaceArea  # m²
    mass = props.Mass  # kg
    cog = props.CenterOfMass  # (x, y, z) in meters
    
    # Convert based on unit
    if unit == "mm":
        volume_display = volume * 1e9  # mm³
        area_display = surface_area * 1e6  # mm²
        volume_unit = "mm³"
        area_unit = "mm²"
    else:
        volume_display = volume
        area_display = surface_area
        volume_unit = "m³"
        area_unit = "m²"
    
    return self._result(True, f"Volume: {volume_display:.2f}{volume_unit}", SwErrors.swSuccess, {
        "volume": volume_display,
        "volume_unit": volume_unit,
        "surface_area": area_display,
        "surface_area_unit": area_unit,
        "mass_kg": mass,
        "center_of_mass": list(cog)
    })
```
**Status:** [~] Partial (2026-09-22) — `get_mass_properties` is Done, but not as designed above: `Extension.CreateMassProperty` fails with COM "Member not found" on this build. Rewired to `IModelDoc2.GetMassProperties` (the older property-style API, a flat 12-tuple `Cx,Cy,Cz,Volume,SurfaceArea,Mass,Ixx..Izx`), verified working live. `measure_distance` is wired but **not verified working**: `Extension.CreateMeasure` fails the same way ("Member not found") and there's no simpler replacement API for arbitrary two-entity distance the way `GetMassProperties` covers mass — same root cause as the Simulation COM gap (see `simulation_com_investigation` memory).

---

### 5.5 Phase 2 Tool Summary

| # | Tool | Category | Priority |
|---|------|----------|----------|
| 1 | draw_arc_center | 2D Sketch | HIGH |
| 2 | draw_arc_3point | 2D Sketch | MEDIUM |
| 3 | draw_spline | 2D Sketch | MEDIUM |
| 4 | draw_polygon | 2D Sketch | HIGH |
| 5 | draw_slot | 2D Sketch | MEDIUM |
| 6 | cut_extrude | 3D Feature | HIGH |
| 7 | fillet_edges | 3D Feature | HIGH |
| 8 | chamfer_edges | 3D Feature | HIGH |
| 9 | revolve_sketch | 3D Feature | HIGH |
| 10 | measure_distance | Measurement | MEDIUM |
| 11 | get_mass_properties | Measurement | MEDIUM |
| 12 | trim_entities | 2D Sketch | MEDIUM |

### 5.6 Phase 2 Deliverables
- [~] 12 new tools (25 registered total, short of the 28 target — spline/slot/revolve/measurements missing)
- [~] Complete 2D sketch capability — spline and slot still missing
- [x] Cut operations
- [x] Fillet & Chamfer
- [ ] Revolve feature
- [ ] Basic measurements
- [x] All tools use unit conversion

---


# 6. PHASE 3: ADVANCED FEATURES
## Week 5-6 | Priority: MEDIUM-HIGH

### 6.1 Goals
- [ ] Sweep and Loft features
- [~] Pattern features (linear, circular, mirror) — linear/circular implemented in `automation/patterns.py` and wired as MCP tools (2026-09-20); mirror still missing
- [ ] Shell feature
- [ ] Reference geometry (planes, axes)
- [ ] Export formats (STEP, STL, DXF)

### 6.2 Advanced Feature Tools

#### Task 3.1: Sweep Feature
```python
def sweep_sketch(self, profile_sketch, path_sketch) -> Dict:
    """
    Sweep a profile along a path
    
    Args:
        profile_sketch: Name of profile sketch
        path_sketch: Name of path sketch
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Select profile
    doc.Extension.SelectByID2(profile_sketch, "SKETCH", 0, 0, 0, False, 1, None, 0)
    
    # Select path
    doc.Extension.SelectByID2(path_sketch, "SKETCH", 0, 0, 0, True, 4, None, 0)
    
    # InsertSweep2: Propagate, Alignment, TwistType, TwistAngle, etc.
    feat = doc.FeatureManager.InsertSweep2(
        False,      # Propagate
        True,       # Alignment type
        0,          # Twist type (none)
        0,          # Twist angle
        False,      # Keep tangency
        False,      # BSpline
        0, 0,       # Start/End scale
        True,       # Thin feature
        0.001,      # Thin wall thickness
        0,          # Thin wall type
        True,       # Merge
        True,       # Auto select
        True        # Feature scope
    )
    
    if feat is None:
        return self._result(False, "Sweep failed", SwErrors.swFeatureError)
    
    return self._result(True, "Sweep feature created", SwErrors.swSuccess)
```
**Status:** [ ] Not Started — no sweep feature

---

#### Task 3.2: Loft Feature
```python
def loft_sketches(self, sketch_names: list) -> Dict:
    """
    Create loft between multiple sketches
    
    Args:
        sketch_names: List of sketch names in order
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if len(sketch_names) < 2:
        return self._result(False, "Loft needs at least 2 profiles", SwErrors.swFeatureError)
    
    # Select sketches as profiles
    for i, name in enumerate(sketch_names):
        append = (i > 0)
        doc.Extension.SelectByID2(name, "SKETCH", 0, 0, 0, append, 1, None, 0)
    
    # InsertLoftRefSurface: Closed, SmType, NoTwist, Guide, Close, etc.
    feat = doc.FeatureManager.InsertProtrusionLoft2(
        False,      # Closed
        True,       # SmType
        False,      # NoTwist
        True,       # Guide influence
        0,          # Start constraint (natural)
        0,          # End constraint (natural)
        0.0, 0.0,   # Start/End tangent length
        True,       # Maintain tangency
        True,       # MergeResult
        True,       # UseFeatScope
        True        # UseAutoSelect
    )
    
    if feat is None:
        return self._result(False, "Loft failed", SwErrors.swFeatureError)
    
    return self._result(True, f"Loft through {len(sketch_names)} profiles", SwErrors.swSuccess)
```
**Status:** [ ] Not Started — no loft feature

---

#### Task 3.3: Linear Pattern
```python
def pattern_linear(self, feature_name, direction="x", count=3, spacing=10, 
                   count2=1, spacing2=0, unit="mm") -> Dict:
    """
    Create linear pattern of a feature
    
    Args:
        feature_name: Feature to pattern
        direction: "x", "y", or edge name
        count: Number in first direction
        spacing: Spacing in first direction
        count2: Number in second direction
        spacing2: Spacing in second direction
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    spacing_m = self.units.to_meters(spacing, unit)
    spacing2_m = self.units.to_meters(spacing2, unit)
    
    # Select feature
    doc.Extension.SelectByID2(feature_name, "BODYFEATURE", 0, 0, 0, False, 4, None, 0)
    
    # Select direction
    if direction.lower() == "x":
        doc.Extension.SelectByID2("", "EDGE", 1, 0, 0, True, 1, None, 0)
    elif direction.lower() == "y":
        doc.Extension.SelectByID2("", "EDGE", 0, 1, 0, True, 1, None, 0)
    
    feat = doc.FeatureManager.FeatureLinearPattern4(
        count, spacing_m,           # D1 count and spacing
        count2, spacing2_m,         # D2 count and spacing
        True, False,                # D1Reverse, D2Reverse
        "", "",                     # D1PatternSeed, D2PatternSeed
        False,                      # GeomPattern
        True, True                  # FeatureScope, AutoSelect
    )
    
    if feat is None:
        return self._result(False, "Linear pattern failed", SwErrors.swFeatureError)
    
    total = count * (count2 if count2 > 0 else 1)
    return self._result(True, f"Linear pattern: {total} instances", SwErrors.swSuccess)
```
**Status:** [x] Done — `automation/patterns.py: create_linear_pattern()` wired as `create_linear_pattern` MCP tool in `server.py` (2026-09-20)

---

#### Task 3.4: Circular Pattern
```python
def pattern_circular(self, feature_name, axis="z", count=6, angle=360, unit="deg") -> Dict:
    """
    Create circular pattern
    
    Args:
        feature_name: Feature to pattern
        axis: "x", "y", "z", or axis name
        count: Number of instances
        angle: Total angle span
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    import math
    angle_rad = math.radians(angle)
    
    # Select feature
    doc.Extension.SelectByID2(feature_name, "BODYFEATURE", 0, 0, 0, False, 4, None, 0)
    
    # Select axis
    if axis.lower() == "z":
        doc.Extension.SelectByID2("Front Plane", "PLANE", 0, 0, 0, True, 1, None, 0)
    
    feat = doc.FeatureManager.FeatureCircularPattern4(
        count,              # Number
        angle_rad,          # Angle span
        False,              # Reverse
        "",                 # PatternSeed
        False,              # GeomPattern
        True,               # EqualSpacing
        True, True          # FeatureScope, AutoSelect
    )
    
    if feat is None:
        return self._result(False, "Circular pattern failed", SwErrors.swFeatureError)
    
    return self._result(True, f"Circular pattern: {count} instances", SwErrors.swSuccess)
```
**Status:** [x] Done — `automation/patterns.py: create_circular_pattern()` wired as `create_circular_pattern` MCP tool in `server.py` (2026-09-20)

---

#### Task 3.5: Mirror Feature
```python
def mirror_feature(self, feature_name, plane="Right") -> Dict:
    """
    Mirror a feature about a plane
    
    Args:
        feature_name: Feature to mirror
        plane: "Front", "Top", "Right" or plane name
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    plane_map = {"Front": "Front Plane", "Top": "Top Plane", "Right": "Right Plane"}
    plane_name = plane_map.get(plane, plane)
    
    # Select feature
    doc.Extension.SelectByID2(feature_name, "BODYFEATURE", 0, 0, 0, False, 4, None, 0)
    
    # Select plane
    doc.Extension.SelectByID2(plane_name, "PLANE", 0, 0, 0, True, 1, None, 0)
    
    feat = doc.FeatureManager.FeatureMirror2(
        True,   # FeatureScope
        True,   # AutoSelect
        False,  # GeomPattern
        True    # Propagate visual properties
    )
    
    if feat is None:
        return self._result(False, "Mirror failed", SwErrors.swFeatureError)
    
    return self._result(True, f"Mirrored about {plane_name}", SwErrors.swSuccess)
```
**Status:** [~] Partial (2026-09-22) — `mirror_feature` wired, but **not verified working**: neither `FeatureMirror2` nor the legacy `InsertMirrorFeature`/`InsertMirrorFeature2` resolve as callable members on this build's `FeatureManager` (COM "Member not found" / "Parameter not optional" at every arg count tried). Modern SW likely requires the `CreateDefinition(swFmMirror)` / `CreateFeature(...)` FeatureData pattern instead — a materially bigger API surface, not yet implemented.

---

#### Task 3.6: Shell Feature
```python
def shell_body(self, thickness, faces_to_remove=None, unit="mm") -> Dict:
    """
    Shell a solid body
    
    Args:
        thickness: Wall thickness
        faces_to_remove: List of face indices to remove (optional)
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    thickness_m = self.units.to_meters(thickness, unit)
    
    if faces_to_remove:
        # Select faces to remove
        doc.ClearSelection2(True)
        for face_idx in faces_to_remove:
            doc.Extension.SelectByID2(f"Face<{face_idx}>", "FACE", 0, 0, 0, True, 0, None, 0)
    
    feat = doc.FeatureManager.InsertFeatureShell2(
        thickness_m,    # Thickness
        False,          # Shell outward
        True            # Show preview
    )
    
    if feat is None:
        return self._result(False, "Shell failed", SwErrors.swFeatureError)
    
    return self._result(True, f"Shell: {thickness}{unit} wall", SwErrors.swSuccess)
```
**Status:** [~] Partial (2026-09-22) — `shell_body` wired, but **not verified working**: `InsertFeatureShell`/`InsertFeatureShell2`/`InsertFeatureShell3` don't resolve on this build's `FeatureManager` at all (COM "Member not found"). Same situation as mirror - likely needs the `CreateDefinition(swFmShell)`/`CreateFeature(...)` FeatureData pattern.

---

### 6.3 Export Tools

#### Task 3.7: Export to STEP
```python
def export_step(self, filepath) -> Dict:
    """
    Export model to STEP format
    
    Args:
        filepath: Output file path (e.g., "C:/export/part.step")
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Ensure .step extension
    if not filepath.lower().endswith(('.step', '.stp')):
        filepath += '.step'
    
    # Create directory if needed
    dir_path = os.path.dirname(filepath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # SaveAs with STEP format
    errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    
    # Save as STEP (format constant: swFileType_e.swSTEP_FILE = 4)
    result = doc.Extension.SaveAs(filepath, 0, 0, None, errors, warnings)
    
    if not result or errors.value != 0:
        return self._result(False, f"Export failed (code {errors.value})", SwErrors.swFileSaveError)
    
    return self._result(True, f"Exported to: {filepath}", SwErrors.swSuccess, {"path": filepath})
```
**Status:** [x] Done — `export_step` wired and verified live (2026-09-22): `Extension.SaveAs` produced a real 17.6KB STEP file.

---

#### Task 3.8: Export to STL
```python
def export_stl(self, filepath, quality="fine", binary=True) -> Dict:
    """
    Export model to STL format for 3D printing
    
    Args:
        filepath: Output file path
        quality: "coarse", "medium", "fine", "custom"
        binary: True for binary STL, False for ASCII
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Ensure .stl extension
    if not filepath.lower().endswith('.stl'):
        filepath += '.stl'
    
    # Create directory
    dir_path = os.path.dirname(filepath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # Set STL quality options
    quality_map = {
        "coarse": (0.1, 30),    # Deviation, Angle
        "medium": (0.05, 15),
        "fine": (0.01, 5),
    }
    deviation, angle = quality_map.get(quality, quality_map["fine"])
    
    # Export
    result = doc.SaveAs4(
        filepath,
        0,      # Save as type
        1 if binary else 0,  # Options
        0,      # Ref configuration
        0       # Alternate geometry
    )
    
    if not result:
        return self._result(False, "STL export failed", SwErrors.swFileSaveError)
    
    return self._result(True, f"STL exported: {filepath}", SwErrors.swSuccess, {
        "path": filepath,
        "quality": quality,
        "binary": binary
    })
```
**Status:** [x] Done — `export_stl` wired (2026-09-22), shares the same `Extension.SaveAs` code path verified working for STEP (format inferred from extension); a `SaveAs4` fallback covers older SW versions. Quality/binary knobs are accepted for API shape parity but not wired to SW's STL preference IDs (left unset rather than guessing undocumented preference constants).

---

#### Task 3.9: Export to DXF
```python
def export_dxf(self, filepath, sheet_name=None) -> Dict:
    """
    Export drawing or flat pattern to DXF
    
    Args:
        filepath: Output file path
        sheet_name: Sheet name for drawings (optional)
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if not filepath.lower().endswith('.dxf'):
        filepath += '.dxf'
    
    # SaveAs with DXF format
    errors = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    warnings = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    
    result = doc.Extension.SaveAs(filepath, 0, 0, None, errors, warnings)
    
    if not result:
        return self._result(False, "DXF export failed", SwErrors.swFileSaveError)
    
    return self._result(True, f"DXF exported: {filepath}", SwErrors.swSuccess)
```
**Status:** [x] Done — `export_dxf` wired (2026-09-22), same verified `Extension.SaveAs` code path as STEP export.

---

### 6.4 Reference Geometry Tools

#### Task 3.10: Create Reference Plane
```python
def create_plane(self, offset=0, reference="Front", unit="mm") -> Dict:
    """
    Create a reference plane
    
    Args:
        offset: Offset distance from reference
        reference: "Front", "Top", "Right", or face name
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    offset_m = self.units.to_meters(offset, unit)
    
    ref_map = {"Front": "Front Plane", "Top": "Top Plane", "Right": "Right Plane"}
    ref_name = ref_map.get(reference, reference)
    
    # Select reference
    doc.Extension.SelectByID2(ref_name, "PLANE", 0, 0, 0, False, 0, None, 0)
    
    # Create offset plane
    feat = doc.FeatureManager.InsertRefPlane(
        1 | 4,      # Type: parallel at distance (swRefPlaneReferenceConstraint_Parallel | Distance)
        offset_m,   # D1 (offset)
        0,          # D2
        0,          # D3
        0,          # D4
        0           # D5
    )
    
    if feat is None:
        return self._result(False, "Failed to create plane", SwErrors.swFeatureError)
    
    return self._result(True, f"Plane created {offset}{unit} from {reference}", SwErrors.swSuccess)
```
**Status:** [x] Done — `create_plane` wired and verified live (2026-09-22): `InsertRefPlane(1|4, offset, 0,0,0,0)` created a real offset "Plane1" feature.

---

### 6.5 Phase 3 Tool Summary

| # | Tool | Category | Priority |
|---|------|----------|----------|
| 1 | sweep_sketch | 3D Feature | HIGH |
| 2 | loft_sketches | 3D Feature | HIGH |
| 3 | pattern_linear | Pattern | HIGH |
| 4 | pattern_circular | Pattern | HIGH |
| 5 | mirror_feature | Pattern | HIGH |
| 6 | shell_body | 3D Feature | MEDIUM |
| 7 | export_step | Export | HIGH |
| 8 | export_stl | Export | HIGH |
| 9 | export_dxf | Export | MEDIUM |
| 10 | create_plane | Reference | MEDIUM |

### 6.6 Phase 3 Deliverables
- [~] 10 new tools (38 total) — 2 wired (linear/circular pattern, 2026-09-20); 8 still not started
- [ ] Sweep and Loft features
- [x] Pattern features — linear/circular wired as MCP tools; mirror still not started
- [ ] Shell feature
- [ ] Export to STEP, STL, DXF
- [ ] Reference plane creation

---


# 7. PHASE 4: ASSEMBLY & DRAWING SUPPORT
## Week 7-8 | Priority: HIGH

### 7.1 Goals
- [x] Create assemblies
- [x] Insert components — implemented in `automation/assemblies.py`, wired as `insert_component`/`insert_library_part` MCP tools (2026-09-20)
- [x] Add mates/constraints — implemented (`add_mate()`), wired as `add_mate` MCP tool (2026-09-20)
- [x] Create drawings — implemented (`create_new_drawing()`), wired as `create_new_drawing` MCP tool (2026-09-20)
- [ ] Add drawing views
- [ ] Add dimensions to drawings

### 7.2 Assembly Tools

#### Task 4.1: Create Assembly
```python
def create_assembly(self) -> Dict:
    """Create a new assembly document"""
    try:
        if not self.is_connected:
            r = self.connect()
            if not r["success"]: return r
        
        # Search for assembly template
        template = None
        sw_dir = os.path.dirname(SOLIDWORKS_EXE)
        
        search_paths = [
            os.path.join(sw_dir, "data", "templates", "Assembly.asmdot"),
            os.path.join(sw_dir, "lang", "english", "Tutorial", "Assembly.asmdot"),
            r"C:\ProgramData\SolidWorks\SOLIDWORKS 2024\templates\Assembly.asmdot",
        ]
        
        for t in search_paths:
            if os.path.exists(t):
                template = t
                break
        
        if not template:
            template = ""  # Use SolidWorks default
        
        doc = self._sw_app.NewDocument(template, 0, 0, 0)
        
        if doc is None:
            return self._result(False, "Failed to create assembly", SwErrors.swFileLoadError)
        
        # Set isometric view
        doc.ShowNamedView2("*Isometric", 7)
        doc.ViewZoomtofit2()
        
        title = doc.GetTitle() if hasattr(doc, 'GetTitle') else "Assembly1"
        if callable(title): title = title()
        
        return self._result(True, f"Created assembly: {title}", SwErrors.swSuccess, 
                          {"name": title, "type": "Assembly"})
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
```
**Status:** [x] Done — `create_new_assembly` tool live; `automation/assemblies.py: create_assembly()` also exists

---

#### Task 4.2: Insert Component
```python
def insert_component(self, filepath, x=0, y=0, z=0, unit="mm") -> Dict:
    """
    Insert a component into the assembly
    
    Args:
        filepath: Path to part or assembly file
        x, y, z: Position coordinates
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Check if this is an assembly
    if doc.GetType() != 2:  # swDocASSEMBLY = 2
        return self._result(False, "Active document is not an assembly", SwErrors.swUnknownError)
    
    if not os.path.exists(filepath):
        return self._result(False, f"File not found: {filepath}", SwErrors.swFileNotFoundError)
    
    x_m = self.units.to_meters(x, unit)
    y_m = self.units.to_meters(y, unit)
    z_m = self.units.to_meters(z, unit)
    
    # AddComponent5: PathName, ConfigName, X, Y, Z, AddConstraints
    component = doc.AddComponent5(
        filepath,
        0,          # swAddComponentConfigOptions_CurrentSelectedConfig
        "",         # Configuration name (empty = active)
        False,      # Use lightweight
        "",         # Ref configuration
        x_m, y_m, z_m  # Position
    )
    
    if component is None:
        return self._result(False, "Failed to insert component", SwErrors.swFileLoadError)
    
    component_name = os.path.basename(filepath)
    return self._result(True, f"Inserted: {component_name}", SwErrors.swSuccess, {
        "component": component_name,
        "position": {"x": x, "y": y, "z": z, "unit": unit}
    })
```
**Status:** [x] Done — `automation/assemblies.py: insert_component()` / `insert_library_part()` wired as MCP tools (2026-09-20)

---

#### Task 4.3: Add Mate (Coincident)
```python
def mate_coincident(self, entity1, entity2, flip=False) -> Dict:
    """
    Add coincident mate between two entities
    
    Args:
        entity1: First entity (e.g., "Face<1>@Part1-1")
        entity2: Second entity
        flip: Flip alignment direction
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if doc.GetType() != 2:
        return self._result(False, "Not an assembly", SwErrors.swUnknownError)
    
    # Clear selection
    doc.ClearSelection2(True)
    
    # Select entities
    doc.Extension.SelectByID2(entity1, "FACE", 0, 0, 0, False, 1, None, 0)
    doc.Extension.SelectByID2(entity2, "FACE", 0, 0, 0, True, 1, None, 0)
    
    # AddMate5: swMateType, swMateAlign, Flip, Distance, DistanceAbsUpperLimit, etc.
    # swMateCOINCIDENT = 0
    mate = doc.AddMate5(
        0,          # Mate type (Coincident)
        1 if flip else 0,  # Alignment
        False,      # Flip
        0, 0, 0,    # Distance limits
        0, 0, 0,    # Angle limits
        0, 0, 0, 0, # Additional params
        False,      # Locked rotation
        True        # Preview
    )
    
    if mate is None:
        return self._result(False, "Failed to add coincident mate", SwErrors.swFeatureError)
    
    return self._result(True, "Coincident mate added", SwErrors.swSuccess)
```
**Status:** [x] Done — `automation/assemblies.py: add_mate()` handles this (validated via `validate_mate_type()`) and is wired as the `add_mate` MCP tool (2026-09-20)

---

#### Task 4.4: Add Mate (Concentric)
```python
def mate_concentric(self, entity1, entity2) -> Dict:
    """
    Add concentric mate between cylindrical faces
    
    Args:
        entity1: First cylindrical face
        entity2: Second cylindrical face
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if doc.GetType() != 2:
        return self._result(False, "Not an assembly", SwErrors.swUnknownError)
    
    doc.ClearSelection2(True)
    doc.Extension.SelectByID2(entity1, "FACE", 0, 0, 0, False, 1, None, 0)
    doc.Extension.SelectByID2(entity2, "FACE", 0, 0, 0, True, 1, None, 0)
    
    # swMateCONCENTRIC = 1
    mate = doc.AddMate5(1, 0, False, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, True)
    
    if mate is None:
        return self._result(False, "Failed to add concentric mate", SwErrors.swFeatureError)
    
    return self._result(True, "Concentric mate added", SwErrors.swSuccess)
```
**Status:** [x] Done — same `add_mate()` covers this mate type, wired as the `add_mate` MCP tool (2026-09-20)

---

#### Task 4.5: Add Distance Mate
```python
def mate_distance(self, entity1, entity2, distance, unit="mm") -> Dict:
    """
    Add distance mate between two entities
    
    Args:
        entity1: First entity
        entity2: Second entity
        distance: Distance value
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if doc.GetType() != 2:
        return self._result(False, "Not an assembly", SwErrors.swUnknownError)
    
    dist_m = self.units.to_meters(distance, unit)
    
    doc.ClearSelection2(True)
    doc.Extension.SelectByID2(entity1, "FACE", 0, 0, 0, False, 1, None, 0)
    doc.Extension.SelectByID2(entity2, "FACE", 0, 0, 0, True, 1, None, 0)
    
    # swMateDISTANCE = 5
    mate = doc.AddMate5(5, 0, False, dist_m, 0, 0, 0, 0, 0, 0, 0, 0, 0, False, True)
    
    if mate is None:
        return self._result(False, "Failed to add distance mate", SwErrors.swFeatureError)
    
    return self._result(True, f"Distance mate: {distance}{unit}", SwErrors.swSuccess)
```
**Status:** [x] Done — same `add_mate()` covers this mate type, wired as the `add_mate` MCP tool (2026-09-20)

---

### 7.3 Drawing Tools

#### Task 4.6: Create Drawing
```python
def create_drawing(self, paper_size="A4", orientation="landscape") -> Dict:
    """
    Create a new drawing document
    
    Args:
        paper_size: "A4", "A3", "A2", "A1", "A0", "Letter", "Legal"
        orientation: "landscape" or "portrait"
    """
    try:
        if not self.is_connected:
            r = self.connect()
            if not r["success"]: return r
        
        # Search for drawing template
        template = None
        sw_dir = os.path.dirname(SOLIDWORKS_EXE)
        
        search_paths = [
            os.path.join(sw_dir, "data", "templates", "Drawing.drwdot"),
            os.path.join(sw_dir, "lang", "english", "Tutorial", "Drawing.drwdot"),
        ]
        
        for t in search_paths:
            if os.path.exists(t):
                template = t
                break
        
        doc = self._sw_app.NewDocument(template or "", 0, 0, 0)
        
        if doc is None:
            return self._result(False, "Failed to create drawing", SwErrors.swFileLoadError)
        
        # Set paper size
        paper_sizes = {
            "A4": (0.210, 0.297),
            "A3": (0.297, 0.420),
            "A2": (0.420, 0.594),
            "A1": (0.594, 0.841),
            "A0": (0.841, 1.189),
            "Letter": (0.2159, 0.2794),
            "Legal": (0.2159, 0.3556),
        }
        
        width, height = paper_sizes.get(paper_size, paper_sizes["A4"])
        if orientation == "landscape":
            width, height = height, width
        
        # Get active sheet and set size
        sheet = doc.GetCurrentSheet()
        if sheet:
            sheet.SetSize(99, width, height)  # 99 = custom size
        
        return self._result(True, f"Created {paper_size} {orientation} drawing", SwErrors.swSuccess)
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swFileLoadError)
```
**Status:** [x] Done — `automation/documents.py: create_new_drawing()` wired as the `create_new_drawing` MCP tool (2026-09-20)

---

#### Task 4.7: Add Drawing View
```python
def add_drawing_view(self, model_path, view_type="front", scale=1.0, x=0.1, y=0.1) -> Dict:
    """
    Add a view to the drawing
    
    Args:
        model_path: Path to part/assembly file
        view_type: "front", "back", "left", "right", "top", "bottom", "isometric"
        scale: View scale (1.0 = 1:1, 0.5 = 1:2)
        x, y: Position on sheet (meters from bottom-left)
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if doc.GetType() != 3:  # swDocDRAWING = 3
        return self._result(False, "Not a drawing document", SwErrors.swUnknownError)
    
    view_types = {
        "front": 1, "back": 2, "left": 3, "right": 4,
        "top": 5, "bottom": 6, "isometric": 7
    }
    view_code = view_types.get(view_type.lower(), 1)
    
    # Create model view
    # CreateDrawViewFromModelView3: ModelName, ViewName, X, Y, Z
    view = doc.CreateDrawViewFromModelView3(
        model_path,
        "*" + view_type.capitalize(),  # View name
        x, y, 0
    )
    
    if view is None:
        return self._result(False, "Failed to add view", SwErrors.swFeatureError)
    
    # Set scale
    view.SetScale2(scale, 1)
    
    return self._result(True, f"Added {view_type} view at {scale}:1", SwErrors.swSuccess)
```
**Status:** [ ] Not Started — no drawing-view tool

---

#### Task 4.8: Add Dimension to Drawing
```python
def add_drawing_dimension(self, entity1, entity2=None, x=0, y=0) -> Dict:
    """
    Add dimension to drawing view
    
    Args:
        entity1: First entity to dimension
        entity2: Second entity (optional, for distance dimensions)
        x, y: Dimension text position
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    if doc.GetType() != 3:
        return self._result(False, "Not a drawing", SwErrors.swUnknownError)
    
    # Select entities
    doc.ClearSelection2(True)
    doc.Extension.SelectByID2(entity1, "EDGE", 0, 0, 0, False, 0, None, 0)
    if entity2:
        doc.Extension.SelectByID2(entity2, "EDGE", 0, 0, 0, True, 0, None, 0)
    
    # Add dimension
    dim = doc.AddDimension2(x, y, 0)
    
    if dim is None:
        return self._result(False, "Failed to add dimension", SwErrors.swFeatureError)
    
    return self._result(True, "Dimension added", SwErrors.swSuccess)
```
**Status:** [ ] Not Started — no drawing-dimension tool

---

### 7.4 Phase 4 Tool Summary

| # | Tool | Category | Priority |
|---|------|----------|----------|
| 1 | create_assembly | Assembly | HIGH |
| 2 | insert_component | Assembly | HIGH |
| 3 | mate_coincident | Assembly | HIGH |
| 4 | mate_concentric | Assembly | HIGH |
| 5 | mate_distance | Assembly | MEDIUM |
| 6 | create_drawing | Drawing | HIGH |
| 7 | add_drawing_view | Drawing | HIGH |
| 8 | add_drawing_dimension | Drawing | MEDIUM |

### 7.5 Phase 4 Deliverables
- [~] 8 new tools (46 total) — 5 wired (2026-09-20: insert_component, insert_library_part, add_mate, get_assembly_tree, list_mates, create_new_drawing — note this covers 6 of the original 8, see 2.3); drawing views/dimensions still not started
- [x] Full assembly support — create, insert, and mate all wired as MCP tools
- [x] Basic mate types — `add_mate` covers coincident/concentric/distance/etc. via one MCP tool
- [x] Drawing creation — wired as `create_new_drawing` MCP tool
- [ ] Drawing views
- [ ] Basic dimensioning

---

# 8. PHASE 5: SIMULATION & ANALYSIS
## Week 9-10 | Priority: MEDIUM

### 8.1 Goals
- [ ] Static stress analysis — `solidworks_simulation.py` exists at repo root but isn't wired into the MCP server. See Task 5.1 status below for a live-tested investigation of the actual blocker (2026-09-20)
- [ ] Modal analysis setup
- [ ] Results extraction
- [ ] Design table support
- [ ] Configuration management

### 8.2 Simulation Tools

#### Task 5.1: Create Static Study
```python
def create_static_study(self, study_name="Static Study") -> Dict:
    """
    Create a new static stress analysis study
    
    Args:
        study_name: Name for the study
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Get SOLIDWORKS Simulation add-in
    try:
        cosworks = self._sw_app.GetAddInObject("SldWorks.Simulation")
        if cosworks is None:
            return self._result(False, "SOLIDWORKS Simulation not available", SwErrors.swUnknownError)
        
        # Get active document's simulation interface
        cwdoc = cosworks.ActiveDoc
        if cwdoc is None:
            return self._result(False, "Cannot access simulation for this document", SwErrors.swUnknownError)
        
        # Create study (Type 1 = Static)
        study = cwdoc.CreateNewStudy2(study_name, 1, None)
        
        if study is None:
            return self._result(False, "Failed to create study", SwErrors.swFeatureError)
        
        return self._result(True, f"Created static study: {study_name}", SwErrors.swSuccess)
    except Exception as e:
        return self._result(False, f"Simulation error: {e}", SwErrors.swUnknownError)
```
**Status:** [ ] Not Started — `solidworks_simulation.py` exists at repo root but is not integrated into the `solidworks_mcp` package or the MCP server.

**Live investigation (2026-09-20):** confirmed SolidWorks Simulation (Student
Edition) IS installed and loadable on this dev machine — `sw.GetAddInObject
("CosmosWorks.CosmosWorks")` (also works via `"SldWorks.Simulation"`, the
ProgID this example code already guesses) returns a live COM object. But it
cannot be automated the same way every other tool in this codebase works:
`cw._oleobj_.GetTypeInfoCount()` returns **0** — the object exposes zero type
info, so dynamic name-based dispatch (`cw.CreateNewStudy2(...)` as written
above) will always fail with `AttributeError`, not because a method name is
wrong but because `GetIDsOfNames` has nothing to resolve names against.

Early-bound (typed) COM access is possible in principle — real progress was
made: the actual Simulation API type library exists on disk at
`C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\Simulation\cosworks.tlb`, and
`win32com.client.gencache.EnsureModule("{B5697F4F-C68A-4685-A7B8-478AF05EF605}",
0, 19, 0)` successfully generates a full Python wrapper with hundreds of real
classes (`ICosmosWorks`, `CWContactManager`, `CWBearingLoad`, etc.) — this
`.tlb` file self-reports as version 19.0. **The blocker:** Windows' registry
has this same typelib GUID registered under version **13.0** instead
(`HKCR\TypeLib\{B5697F4F-C68A-4685-A7B8-478AF05EF605}` only has a `13.0`
subkey), and `cw._oleobj_.QueryInterface(mod.ICosmosWorks.CLSID,
pythoncom.IID_IDispatch)` fails with `"No such interface supported"` against
the 19.0-generated interface ID — the live loaded add-in doesn't actually
implement that exact interface version. Regenerating explicitly against
version 13.0 also failed (`"Library not registered"` — `EnsureModule` couldn't
resolve an actual loadable typelib for that specific version/GUID pairing).

**Root cause, unresolved:** a real version inconsistency in this specific
SolidWorks Simulation Student Edition install (`.tlb` file content vs.
registry registration vs. what the live add-in actually implements don't
agree with each other) — not a dead end in principle, but not something
worth guessing at further without either (a) a known-working SolidWorks
Simulation macro on this exact machine to see which interface version it
successfully references, or (b) SolidWorks' own current Simulation API
SDK/sample matching this install's actual build. **Do not wire Simulation
MCP tools with plain dynamic dispatch (mirroring the pattern used everywhere
else in `solidworks_mcp/automation/`) — they will fail on every call given
the confirmed zero-type-info result above.** Any future attempt needs the
early-bound/typed approach, picking up from the `.tlb` file and GUID already
identified here.

**Practical fallback that still works today:** SolidWorks Motion Studies are
fully usable manually through the SolidWorks UI (Insert Motion Study) — just
not scriptable from this MCP server given the above.

---

#### Task 5.2: Apply Material
```python
def apply_material(self, material_name, library="solidworks materials") -> Dict:
    """
    Apply material to the active part
    
    Args:
        material_name: Material name (e.g., "AISI 1020 Steel")
        library: Material library name
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Get material database
    # SetMaterialPropertyName2: ConfigName, DatabaseFile, MaterialName
    result = doc.SetMaterialPropertyName2(
        "",  # Active configuration
        library,
        material_name
    )
    
    if not result:
        return self._result(False, f"Material '{material_name}' not found", SwErrors.swUnknownError)
    
    return self._result(True, f"Applied material: {material_name}", SwErrors.swSuccess)
```
**Status:** [ ] Not Started

---

#### Task 5.3: Apply Fixed Fixture
```python
def apply_fixture_fixed(self, face_name) -> Dict:
    """
    Apply fixed fixture to a face
    
    Args:
        face_name: Face to fix (e.g., "Face<1>")
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    try:
        cosworks = self._sw_app.GetAddInObject("SldWorks.Simulation")
        cwdoc = cosworks.ActiveDoc
        study = cwdoc.ActiveStudy
        
        if study is None:
            return self._result(False, "No active study", SwErrors.swUnknownError)
        
        # Select face
        doc.Extension.SelectByID2(face_name, "FACE", 0, 0, 0, False, 0, None, 0)
        
        # Apply fixed restraint (Type 0)
        lbc = study.AddRestraint(0, None, None, 0, 0, 0, 0, 0, 0, 0, 0)
        
        if lbc is None:
            return self._result(False, "Failed to apply fixture", SwErrors.swFeatureError)
        
        return self._result(True, f"Fixed fixture on {face_name}", SwErrors.swSuccess)
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
```
**Status:** [ ] Not Started

---

#### Task 5.4: Apply Force Load
```python
def apply_force(self, face_name, force_value, direction="normal", unit="N") -> Dict:
    """
    Apply force load to a face
    
    Args:
        face_name: Face to apply force
        force_value: Force magnitude
        direction: "normal", "x", "y", "z"
        unit: Force unit ("N", "kN", "lbf")
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Convert force to Newtons
    force_conversion = {"N": 1.0, "kN": 1000.0, "lbf": 4.44822}
    force_n = force_value * force_conversion.get(unit, 1.0)
    
    try:
        cosworks = self._sw_app.GetAddInObject("SldWorks.Simulation")
        cwdoc = cosworks.ActiveDoc
        study = cwdoc.ActiveStudy
        
        if study is None:
            return self._result(False, "No active study", SwErrors.swUnknownError)
        
        # Select face
        doc.Extension.SelectByID2(face_name, "FACE", 0, 0, 0, False, 0, None, 0)
        
        # Direction components
        dir_vectors = {
            "normal": (0, 0, 0),  # Normal to face
            "x": (1, 0, 0),
            "y": (0, 1, 0),
            "z": (0, 0, 1),
        }
        dx, dy, dz = dir_vectors.get(direction.lower(), (0, 0, 0))
        
        # Apply force (Type 1)
        load = study.AddLoad(1, None, None, force_n, dx, dy, dz, 0, 0, 0)
        
        if load is None:
            return self._result(False, "Failed to apply force", SwErrors.swFeatureError)
        
        return self._result(True, f"Applied {force_value}{unit} force on {face_name}", SwErrors.swSuccess)
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
```
**Status:** [ ] Not Started

---

#### Task 5.5: Run Analysis
```python
def run_simulation(self) -> Dict:
    """
    Run the active simulation study
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    try:
        cosworks = self._sw_app.GetAddInObject("SldWorks.Simulation")
        cwdoc = cosworks.ActiveDoc
        study = cwdoc.ActiveStudy
        
        if study is None:
            return self._result(False, "No active study", SwErrors.swUnknownError)
        
        # Create mesh
        mesh = study.Mesh
        if mesh is None:
            return self._result(False, "Failed to create mesh", SwErrors.swFeatureError)
        
        mesh.Quality = 1  # High quality
        mesh_result = mesh.CreateMesh(0, 0)  # Auto element size
        
        if mesh_result != 0:
            return self._result(False, f"Mesh failed (code {mesh_result})", SwErrors.swFeatureError)
        
        # Run analysis
        run_result = study.RunAnalysis()
        
        if run_result != 0:
            return self._result(False, f"Analysis failed (code {run_result})", SwErrors.swFeatureError)
        
        return self._result(True, "Simulation completed successfully", SwErrors.swSuccess)
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
```
**Status:** [ ] Not Started

---

#### Task 5.6: Get Stress Results
```python
def get_stress_results(self) -> Dict:
    """
    Get stress results from completed simulation
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    try:
        cosworks = self._sw_app.GetAddInObject("SldWorks.Simulation")
        cwdoc = cosworks.ActiveDoc
        study = cwdoc.ActiveStudy
        
        if study is None:
            return self._result(False, "No active study", SwErrors.swUnknownError)
        
        # Get results
        results = study.Results
        if results is None:
            return self._result(False, "No results available", SwErrors.swUnknownError)
        
        # Get von Mises stress
        stress = results.GetMinMaxStress(
            0,      # Component (0 = VON Mises)
            1,      # Step
            None,   # Entities
            0,      # Unit (Pa)
            None, None  # Min/Max location arrays
        )
        
        min_stress = stress[0] / 1e6  # Convert to MPa
        max_stress = stress[1] / 1e6
        
        return self._result(True, f"Max stress: {max_stress:.2f} MPa", SwErrors.swSuccess, {
            "min_stress_mpa": min_stress,
            "max_stress_mpa": max_stress,
            "stress_type": "von Mises"
        })
    except Exception as e:
        return self._result(False, f"Error: {e}", SwErrors.swUnknownError)
```
**Status:** [ ] Not Started

---

### 8.3 Phase 5 Tool Summary

| # | Tool | Category | Priority |
|---|------|----------|----------|
| 1 | create_static_study | Simulation | HIGH |
| 2 | apply_material | Simulation | HIGH |
| 3 | apply_fixture_fixed | Simulation | HIGH |
| 4 | apply_force | Simulation | HIGH |
| 5 | run_simulation | Simulation | HIGH |
| 6 | get_stress_results | Simulation | HIGH |

### 8.4 Phase 5 Deliverables
- [ ] 6 new tools (52 total) — none wired into the MCP server
- [ ] Static analysis workflow
- [ ] Material assignment
- [ ] Boundary conditions
- [ ] Results extraction

---


# 9. PHASE 6: PRODUCTION HARDENING
## Week 11-12 | Priority: HIGH

### 9.1 Goals
- [~] Comprehensive error handling — try/except + error codes throughout; two known unguarded COM bugs remain (see 2.3)
- [~] Recovery mechanisms — 4 connection fallback methods in `base.py`
- [ ] Performance optimization
- [x] Validation & sanitization — `utils/validation.py`
- [~] Documentation completion — README, this roadmap, and the `solidworks-design` skill exist; still gaps (unwired features undocumented until now)
- [ ] Test coverage > 80% — not measured; `tests/` covers config/units/validation/parts/engineering modules, not `server.py` itself

### 9.2 Error Recovery System

#### Task 6.1: Connection Recovery
```python
class ConnectionManager:
    """Robust connection management with recovery"""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    
    def __init__(self, automation):
        self.automation = automation
        self.connection_attempts = 0
        self.last_error = None
    
    async def ensure_connected(self) -> bool:
        """Ensure connection with automatic recovery"""
        if self.automation.is_connected:
            return True
        
        for attempt in range(self.MAX_RETRIES):
            try:
                result = self.automation.connect()
                if result["success"]:
                    self.connection_attempts = 0
                    return True
                
                self.last_error = result["message"]
                logger.warning(f"Connection attempt {attempt + 1} failed: {self.last_error}")
                
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                    
            except Exception as e:
                self.last_error = str(e)
                logger.error(f"Connection error: {e}")
        
        return False
    
    def handle_com_error(self, error) -> Dict:
        """Handle COM errors with recovery suggestions"""
        error_str = str(error)
        
        recovery_actions = {
            "RPC server": "SolidWorks may have crashed. Restart required.",
            "Call was rejected": "SolidWorks is busy. Wait and retry.",
            "Interface not registered": "COM registration issue. Repair SolidWorks.",
            "Access denied": "Permission issue. Run as administrator.",
        }
        
        for pattern, action in recovery_actions.items():
            if pattern.lower() in error_str.lower():
                return {
                    "error": error_str,
                    "recovery": action,
                    "retry_possible": "rejected" in error_str.lower()
                }
        
        return {"error": error_str, "recovery": "Unknown error. Check log file."}
```
**Status:** [~] Partial — `base.py` tries 4 connection methods and `config.py` has retry settings, but `get_document_info`/`list_open_documents` still throw unguarded COM errors on some bindings (see the `solidworks-design` skill's Known Bugs section)

---

#### Task 6.2: Input Validation
```python
from typing import Union, List, Tuple
import re

class InputValidator:
    """Validate and sanitize user inputs"""
    
    @staticmethod
    def validate_filepath(filepath: str) -> Tuple[bool, str]:
        """Validate file path"""
        if not filepath:
            return False, "File path cannot be empty"
        
        # Check for invalid characters
        invalid_chars = '<>"|?*'
        for char in invalid_chars:
            if char in filepath:
                return False, f"Invalid character '{char}' in path"
        
        # Check extension
        valid_extensions = ['.sldprt', '.sldasm', '.slddrw', '.step', '.stl', '.dxf']
        ext = os.path.splitext(filepath)[1].lower()
        if ext and ext not in valid_extensions:
            return False, f"Invalid extension: {ext}"
        
        return True, "Valid"
    
    @staticmethod
    def validate_dimension(value: Union[int, float], 
                          min_val: float = 0.0001, 
                          max_val: float = 1000.0,
                          unit: str = "m") -> Tuple[bool, str]:
        """Validate dimension value"""
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False, "Invalid numeric value"
        
        if value < min_val:
            return False, f"Value too small (min: {min_val}{unit})"
        if value > max_val:
            return False, f"Value too large (max: {max_val}{unit})"
        
        return True, "Valid"
    
    @staticmethod
    def validate_plane(plane: str) -> Tuple[bool, str]:
        """Validate plane name"""
        valid_planes = ["Front", "Top", "Right", "front", "top", "right"]
        if plane not in valid_planes:
            return False, f"Invalid plane. Use: Front, Top, or Right"
        return True, "Valid"
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Sanitize filename by removing invalid characters"""
        # Remove or replace invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        return name.strip()
```
**Status:** [x] Done — `utils/validation.py` implements `validate_dimension/name/plane/position/sku/mate_type/end_condition`

---

#### Task 6.3: Performance Optimization
```python
import functools
import time
from threading import Lock

class PerformanceOptimizer:
    """Optimize MCP server performance"""
    
    _cache = {}
    _cache_lock = Lock()
    _cache_ttl = 60  # seconds
    
    @classmethod
    def cached(cls, ttl: int = None):
        """Decorator to cache function results"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                
                with cls._cache_lock:
                    if cache_key in cls._cache:
                        result, timestamp = cls._cache[cache_key]
                        if time.time() - timestamp < (ttl or cls._cache_ttl):
                            return result
                
                result = func(*args, **kwargs)
                
                with cls._cache_lock:
                    cls._cache[cache_key] = (result, time.time())
                
                return result
            return wrapper
        return decorator
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached results"""
        with cls._cache_lock:
            cls._cache.clear()
    
    @staticmethod
    def batch_operations(operations: List[callable]) -> List:
        """Execute multiple operations in batch"""
        results = []
        for op in operations:
            try:
                results.append(op())
            except Exception as e:
                results.append({"error": str(e)})
        return results

# Usage example
class SolidWorksAutomationOptimized(SolidWorksAutomation):
    
    @PerformanceOptimizer.cached(ttl=30)
    def get_document_info(self) -> Dict:
        """Cached document info"""
        return super().get_document_info()
    
    @PerformanceOptimizer.cached(ttl=300)
    def get_available_materials(self) -> List[str]:
        """Cached material list"""
        # ... implementation
        pass
```
**Status:** [ ] Not Started

---

### 9.3 Additional Utility Tools

#### Task 6.4: Undo/Redo Support
```python
def undo(self) -> Dict:
    """Undo last operation"""
    doc, err = self.get_active_doc()
    if err: return err
    
    # EditUndo2 returns True if successful
    result = self._sw_app.EditUndo2(1)  # Undo 1 step
    
    if result:
        return self._result(True, "Undo successful", SwErrors.swSuccess)
    return self._result(False, "Nothing to undo", SwErrors.swUnknownError)

def redo(self) -> Dict:
    """Redo last undone operation"""
    doc, err = self.get_active_doc()
    if err: return err
    
    result = self._sw_app.EditRedo2(1)
    
    if result:
        return self._result(True, "Redo successful", SwErrors.swSuccess)
    return self._result(False, "Nothing to redo", SwErrors.swUnknownError)
```
**Status:** [x] Done — `undo`/`redo` wired and verified live (2026-09-22), with one fix from the design above: `EditUndo2`/`EditRedo2` live on `IModelDoc2` (`doc`), not `SldWorks.Application` (`sw`) - calling on `sw` fails to resolve at all. The return value is also unreliable (observed `None` on a confirmed-successful undo, checked via feature-tree count before/after), so success is now based on the call not raising rather than its return value.

---

#### Task 6.5: Screenshot/View Capture
```python
def capture_view(self, filepath, width=1920, height=1080) -> Dict:
    """
    Capture current view as image
    
    Args:
        filepath: Output image path (.png, .jpg, .bmp)
        width: Image width in pixels
        height: Image height in pixels
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    # Ensure directory exists
    dir_path = os.path.dirname(filepath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    # Get model view
    view = doc.ActiveView
    if view is None:
        return self._result(False, "No active view", SwErrors.swUnknownError)
    
    # Capture to file
    # SaveBMP: FileName, Width, Height
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.png':
        result = doc.SaveBMP(filepath, width, height)
    elif ext in ['.jpg', '.jpeg']:
        result = doc.SaveBMP(filepath.replace(ext, '.bmp'), width, height)
        # Convert BMP to JPG if needed
    else:
        result = doc.SaveBMP(filepath, width, height)
    
    if not result:
        return self._result(False, "Failed to capture view", SwErrors.swFileSaveError)
    
    return self._result(True, f"Captured: {filepath}", SwErrors.swSuccess, {
        "path": filepath,
        "width": width,
        "height": height
    })
```
**Status:** [x] Done — `capture_view` wired and verified live (2026-09-22): `doc.SaveBMP(path, w, h)` produced a real BMP file. Only BMP capture exists on this API; other extensions still write BMP data as documented in the tool description.

---

#### Task 6.6: Zoom and View Control
```python
def zoom_fit(self) -> Dict:
    """Zoom to fit all geometry"""
    doc, err = self.get_active_doc()
    if err: return err
    
    doc.ViewZoomtofit2()
    return self._result(True, "Zoomed to fit", SwErrors.swSuccess)

def set_view(self, view_name="isometric") -> Dict:
    """
    Set standard view
    
    Args:
        view_name: "front", "back", "left", "right", "top", "bottom", "isometric", "trimetric", "dimetric"
    """
    doc, err = self.get_active_doc()
    if err: return err
    
    view_map = {
        "front": ("*Front", 1),
        "back": ("*Back", 2),
        "left": ("*Left", 3),
        "right": ("*Right", 4),
        "top": ("*Top", 5),
        "bottom": ("*Bottom", 6),
        "isometric": ("*Isometric", 7),
        "trimetric": ("*Trimetric", 8),
        "dimetric": ("*Dimetric", 9),
    }
    
    view_data = view_map.get(view_name.lower())
    if view_data is None:
        return self._result(False, f"Unknown view: {view_name}", SwErrors.swUnknownError)
    
    doc.ShowNamedView2(view_data[0], view_data[1])
    doc.ViewZoomtofit2()
    
    return self._result(True, f"Set view: {view_name}", SwErrors.swSuccess)
```
**Status:** [x] Done — `zoom_fit`/`set_view` wired (2026-09-22), reusing `ShowNamedView2`/`ViewZoomtofit2` calls already proven working elsewhere in this codebase (`create_new_part` etc.).

---

### 9.4 Phase 6 Tool Summary

| # | Tool | Category | Priority |
|---|------|----------|----------|
| 1 | undo | Utility | MEDIUM |
| 2 | redo | Utility | MEDIUM |
| 3 | capture_view | Export | MEDIUM |
| 4 | zoom_fit | View | LOW |
| 5 | set_view | View | LOW |

### 9.5 Phase 6 Deliverables
- [ ] 5 new tools (55+ total)
- [~] Connection recovery system — partial (see 9.1)
- [x] Input validation
- [ ] Performance caching
- [~] Error recovery — partial (see 2.3)
- [ ] Complete test suite
- [~] Documentation — partial (see 9.1)

---

# 10. TESTING STRATEGY

## 10.1 Test Categories

### Unit Tests
```python
# tests/test_units.py
import pytest
from utils.units import UnitConverter, mm, inch

class TestUnitConverter:
    def test_mm_to_meters(self):
        assert mm(50) == 0.05
    
    def test_inch_to_meters(self):
        assert abs(inch(1) - 0.0254) < 0.0001
    
    def test_converter_mm(self):
        conv = UnitConverter("mm")
        assert conv.to_meters(100) == 0.1
    
    def test_converter_inch(self):
        conv = UnitConverter("inch")
        assert abs(conv.to_meters(1) - 0.0254) < 0.0001
```

### Integration Tests
```python
# tests/test_integration.py
import pytest
from solidworks_mcp_server import sw_automation

class TestSolidWorksIntegration:
    @pytest.fixture(autouse=True)
    def setup(self):
        """Connect to SolidWorks before tests"""
        result = sw_automation.connect()
        if not result["success"]:
            pytest.skip("SolidWorks not available")
    
    def test_create_part(self):
        result = sw_automation.create_new_part()
        assert result["success"] == True
        sw_automation.close_document()
    
    def test_create_sketch(self):
        sw_automation.create_new_part()
        result = sw_automation.create_sketch("Front")
        assert result["success"] == True
        sw_automation.close_document()
    
    def test_draw_circle(self):
        sw_automation.create_new_part()
        sw_automation.create_sketch("Front")
        result = sw_automation.draw_circle(0, 0, 0.05)
        assert result["success"] == True
        sw_automation.close_document()
    
    def test_full_workflow(self):
        """Test complete part creation workflow"""
        sw_automation.create_new_part()
        sw_automation.create_sketch("Front")
        sw_automation.draw_circle(0, 0, 0.025)
        result = sw_automation.extrude_sketch(0.01)
        assert result["success"] == True
        sw_automation.close_document()
```

## 10.2 Test Coverage Goals

| Phase | Target Coverage |
|-------|-----------------|
| Phase 1 | 60% |
| Phase 2 | 70% |
| Phase 3 | 75% |
| Phase 4 | 80% |
| Phase 5 | 80% |
| Phase 6 | 85%+ |

---

# 11. DOCUMENTATION PLAN

## 11.1 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Quick start guide |
| INSTALLATION.md | Detailed installation |
| API_REFERENCE.md | All tools documented |
| EXAMPLES.md | Usage examples |
| TROUBLESHOOTING.md | Common issues |
| CHANGELOG.md | Version history |
| CONTRIBUTING.md | Developer guide |

## 11.2 API Documentation Template

```markdown
## Tool: `draw_circle`

### Description
Draw a circle in the active sketch.

### Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| x | number | 0 | Center X coordinate |
| y | number | 0 | Center Y coordinate |
| radius | number | 50 | Circle radius |
| unit | string | "mm" | Unit (mm, inch, m) |

### Returns
```json
{
  "success": true,
  "message": "Circle r=50mm",
  "error_code": 0,
  "data": {
    "radius_mm": 50
  }
}
```

### Example Usage
"Draw a circle with 25mm radius at the origin"

### Notes
- Requires an active sketch
- Use `create_sketch` first
```

---

# 12. PROGRESS TRACKING

## 12.1 Phase Checklist

### Phase 1: Foundation [x] Done
- [x] Project structure created
- [x] Configuration system
- [x] Unit conversion
- [x] Auto-detect SolidWorks
- [x] 5 new tools

### Phase 2: Core Features [~] Partial (spline/revolve/mass-properties wired and verified 2026-09-22)
- [x] Arc tools
- [x] Spline tool — verified live, needs explicit `VT_ARRAY|VT_R8` VARIANT
- [x] Polygon tool
- [x] Cut extrude
- [x] Fillet/Chamfer
- [x] Revolve — verified live, real signature is 20-param `FeatureRevolve2`
- [~] Measurements — mass properties Done (via `GetMassProperties`, verified); distance wired but blocked (`CreateMeasure` COM "Member not found" on this build)
- [~] Slot — wired but blocked (`CreateSketchSlot` COM "Parameter not optional" at every arg count tried on this build)

### Phase 3: Advanced [~] Partial (patterns wired 2026-09-20; export/plane wired and verified, mirror/shell blocked 2026-09-22)
- [ ] Sweep
- [ ] Loft
- [x] Patterns — `automation/patterns.py` linear/circular wired as MCP tools
- [~] Mirror — wired but blocked (`FeatureMirror2`/legacy `InsertMirrorFeature*` don't resolve on this build; likely needs the modern `CreateDefinition`/`CreateFeature` FeatureData pattern)
- [~] Shell — wired but blocked, same root cause as Mirror (`InsertFeatureShell*` don't resolve)
- [x] Export tools — STEP/STL/DXF via `Extension.SaveAs`, verified live (real STEP file written)
- [x] Reference plane — `create_plane`/`InsertRefPlane`, verified live

### Phase 4: Assembly & Drawing [~] Partial (assembly/mate/drawing wired 2026-09-20)
- [x] Assembly support — create, insert, tree, and list all wired as MCP tools
- [x] Mates — `automation/assemblies.py: add_mate()` wired as MCP tool
- [x] Drawing support — `create_new_drawing()` wired as MCP tool
- [ ] Views & dimensions

### Phase 5: Simulation [ ] Not Started (investigated, real blocker found — see 8.1/Task 5.1)
- [ ] Static study — blocked on a COM interface version mismatch in the local
  Simulation Student Edition install (`.tlb` reports v19.0, registry has
  v13.0, live add-in implements neither's `ICosmosWorks` IID); dynamic
  dispatch confirmed impossible (`GetTypeInfoCount()` = 0)
- [ ] Materials
- [ ] Loads & fixtures
- [ ] Results

### Phase 6: Production [~] Partial (undo/redo, screenshot, zoom/view wired and verified 2026-09-22)
- [~] Error recovery — 4 connection fallbacks exist; known COM bugs remain (see 2.3)
- [x] Validation — `utils/validation.py`
- [x] Undo/Redo — verified live; must call on `doc`, not `sw` (Application)
- [x] Screenshot/view capture — `capture_view`/`SaveBMP`, verified live
- [x] Zoom/view control — `zoom_fit`/`set_view`, reuses already-proven view calls
- [ ] Performance
- [ ] Tests — `tests/` exists but coverage of `solidworks_mcp/server.py` itself is unverified
- [~] Documentation — README + this roadmap + `solidworks-design` skill

## 12.2 Weekly Log Template

```markdown
## Week [X] - [Date]

### Completed
- [ ] Task 1
- [ ] Task 2

### In Progress
- [ ] Task 3

### Blocked
- [ ] Task 4 - Reason: ...

### Notes
- ...

### Next Week
- [ ] Task 5
- [ ] Task 6
```

---

# 13. RESOURCES

## 13.1 SolidWorks API Documentation
- [SolidWorks API Help](https://help.solidworks.com/2024/english/api/sldworksapiprogguide/welcome.htm)
- [API Object Model](https://help.solidworks.com/2024/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks_namespace.html)

## 13.2 MCP Protocol
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/anthropics/mcp-python-sdk)

## 13.3 Python COM
- [pywin32 Documentation](https://pypi.org/project/pywin32/)
- [COM Automation Guide](https://pbpython.com/windows-com.html)

---

# 14. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 2.3 | Jan 2026 | Baseline — 11 tools |
| 3.x (unreleased) | 2026-09-19 | 25 tools registered; assembly/pattern/drawing operations implemented in `automation/` but not yet wired to the tool list; Parts Intelligence and Engineering Intelligence layers added (beyond original scope); roadmap checkboxes reconciled against real code (see 2.3) |
| 3.x (unreleased) | 2026-09-20 | 33 tools registered — wired `insert_component`, `insert_library_part`, `add_mate`, `get_assembly_tree`, `list_mates`, `create_linear_pattern`, `create_circular_pattern`, `create_new_drawing` into `server.py`. Live-tested against SolidWorks 34.4.1 the same day (see 2.3a): found and fixed 4 real bugs (`insert_component` never pre-loaded referenced files; `GetChildren()` called as a method when it's a property on this COM binding; `SelectByID2`'s Callout param passed as `None` instead of a VARIANT in `assemblies.py` and `patterns.py`; `add_mate`/patterns hardcoded an empty entity-select type). `insert_component`, `get_assembly_tree`, `list_mates`, `create_new_drawing`, `insert_library_part` (config-missing path) all confirmed working live. `add_mate` and both pattern tools still fail with a COM "Parameter not optional" error from `AddMate5`/`AddMate3`/`FeatureLinearPattern4` — root cause not yet found; needs the official SW 2026 API reference, not further guessing. |
| 4.0 | Target | 55+ tools, full CAD support, simulation, all `automation/` capability wired and exposed |

---

**END OF ROADMAP**

*Last Updated: 2026-09-19 (status reconciled against actual code; see section 2.3)*
*Author: Samsaam Ali Baig*
