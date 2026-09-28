"""Regression tests: COM linked-list traversals must always terminate.

SolidWorks exposes feature trees, open documents and mate chains as linked
lists (``FirstFeature`` / ``GetNextFeature``). A naive ``while node:`` loop over
one of those never terminates when the chain is cyclic, malformed, or a test
double -- a ``MagicMock`` yields a fresh truthy child from every ``GetNext*``
access. Each iteration then retained another object, which grew at ~105MB/s and
OOM-killed the whole machine while running this very suite.

The fakes below are deliberately *cyclic* rather than mocks: a node whose
successor is itself never terminates on its own, but costs no memory, so these
tests prove the iteration bound without needing gigabytes to do it.
"""

from unittest.mock import MagicMock

from solidworks_mcp.automation.assemblies import AssemblyOperations
from solidworks_mcp.automation.documents import DocumentOperations
from solidworks_mcp.automation.features import FeatureOperations
from solidworks_mcp.constants import Defaults, SwErrors
from solidworks_mcp.utils.tree_walk import walk_exhausted

CAP = Defaults.MAX_TREE_WALK


# --- Endless COM chains (cyclic: successor is self) ---

class _CyclicFeature:
    """A feature whose GetNextFeature is itself, so the tree never ends."""

    Name = "Sketch1"
    GetTypeName2 = "ProfileFeature"

    @property
    def GetNextFeature(self):  # noqa: N802 - mirrors the COM API name
        return self


class _CyclicSubFeature:
    """A mate whose GetNextSubFeature is itself."""

    Name = "Mate1"
    GetTypeName2 = "Coincident"

    @property
    def GetNextSubFeature(self):  # noqa: N802 - mirrors the COM API name
        return self


class _CyclicDocument:
    """An open document whose GetNext is itself."""

    GetTitle = "Part1.SLDPRT"
    GetType = 1

    @property
    def GetNext(self):  # noqa: N802 - mirrors the COM API name
        return self


class _MateGroup:
    """The mate folder, holding an endless chain of mates."""

    GetTypeName2 = "MateGroup"
    GetFirstSubFeature = _CyclicSubFeature()


# --- Minimal harnesses for the automation mixins ---

def _result(success, message, error_code=SwErrors.swSuccess, data=None):
    result = {"success": success, "message": message, "error_code": int(error_code)}
    if data:
        result["data"] = data
    return result


class _Features(FeatureOperations):
    def __init__(self, doc):
        self._doc = doc

    def get_active_doc(self):
        return self._doc, None

    _result = staticmethod(_result)


class _Documents(DocumentOperations):
    is_connected = True

    def __init__(self, sw_app):
        self._sw_app = sw_app

    _result = staticmethod(_result)


class _Assemblies(AssemblyOperations):
    def __init__(self, doc):
        self._doc = doc

    def get_active_doc(self):
        return self._doc, None

    _result = staticmethod(_result)


def _endless_doc():
    doc = MagicMock()
    doc.SketchManager.ActiveSketch = None
    doc.FirstFeature = _CyclicFeature()
    return doc


class _FiniteFeature:
    """A well-formed feature tree of `remaining` nodes, then None."""

    def __init__(self, remaining: int, index: int = 1):
        self.Name = f"Sketch{index}"
        self.GetTypeName2 = "ProfileFeature"
        self._remaining = remaining
        self._index = index

    @property
    def GetNextFeature(self):  # noqa: N802 - mirrors the COM API name
        if self._remaining <= 1:
            return None
        return _FiniteFeature(self._remaining - 1, self._index + 1)


def _finite_doc(feature_count: int):
    doc = MagicMock()
    doc.SketchManager.ActiveSketch = None
    doc.FirstFeature = _FiniteFeature(feature_count)
    return doc


# --- A well-formed tree is walked to completion (the bound changes nothing) ---

class TestFiniteTreeIsUnaffected:
    """The cap must not truncate real models, which are far below it."""

    def test_list_features_returns_every_feature(self):
        result = _Features(_finite_doc(7)).list_features()

        assert result["data"]["count"] == 7
        assert [f["name"] for f in result["data"]["features"]] == [
            f"Sketch{i}" for i in range(1, 8)
        ]

    def test_get_sketch_info_counts_every_feature(self):
        info = _Features(_finite_doc(7))._get_sketch_info(_finite_doc(7))

        assert info["feature_count"] == 7
        assert info["sketch_count"] == 7

    def test_find_last_sketch_reaches_the_end(self):
        assert _Features(_finite_doc(7))._find_last_sketch(_finite_doc(7)) == "Sketch7"

    def test_tree_exactly_at_the_cap_is_complete(self):
        info = _Features(_finite_doc(CAP))._get_sketch_info(_finite_doc(CAP))

        assert info["feature_count"] == CAP


# --- The bound itself ---

class TestWalkExhausted:
    def test_allows_iteration_below_the_cap(self):
        assert walk_exhausted(0, "feature tree") is False
        assert walk_exhausted(CAP - 1, "feature tree") is False

    def test_stops_at_the_cap(self):
        assert walk_exhausted(CAP, "feature tree") is True

    def test_respects_an_explicit_limit(self):
        assert walk_exhausted(4, "feature tree", limit=5) is False
        assert walk_exhausted(5, "feature tree", limit=5) is True

    def test_warns_when_the_cap_is_hit(self, caplog):
        walk_exhausted(CAP, "feature tree")

        assert "feature tree" in caplog.text


# --- Walkers terminate on an endless chain ---

class TestFeatureTreeWalkTerminates:
    def test_find_last_sketch_returns(self):
        assert _Features(_endless_doc())._find_last_sketch(_endless_doc()) == "Sketch1"

    def test_get_sketch_info_stops_at_the_cap(self):
        info = _Features(_endless_doc())._get_sketch_info(_endless_doc())

        assert info["feature_count"] == CAP

    def test_list_features_stops_at_the_cap(self):
        result = _Features(_endless_doc()).list_features()

        assert result["success"] is True
        assert result["data"]["count"] == CAP


class TestDocumentListWalkTerminates:
    def test_list_open_documents_stops_at_the_cap(self):
        sw_app = MagicMock()
        sw_app.GetFirstDocument = _CyclicDocument()

        result = _Documents(sw_app).list_open_documents()

        assert result["success"] is True
        assert len(result["data"]["documents"]) == CAP


class TestMateWalkTerminates:
    def test_list_mates_stops_at_the_cap(self):
        doc = MagicMock()
        doc.FeatureManager.GetFeatures.return_value = [_MateGroup()]

        result = _Assemblies(doc).list_mates()

        assert result["success"] is True
        assert result["data"]["count"] == CAP


# --- The mock shape that actually crashed the machine ---

class TestMagicMockTreeIsBounded:
    """An unstubbed MagicMock doc yields an endless feature tree.

    Capped at a small limit so the test cannot allocate much: each MagicMock
    node costs ~100KB, which is exactly why the unbounded version was fatal.
    """

    def test_mock_feature_tree_terminates(self, monkeypatch):
        monkeypatch.setattr(
            "solidworks_mcp.automation.features.walk_exhausted",
            lambda count, what, limit=50: walk_exhausted(count, what, limit=limit),
        )

        info = _Features(MagicMock())._get_sketch_info(MagicMock())

        assert info["feature_count"] == 50
