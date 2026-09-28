"""Tests for reading parameterless COM methods/properties safely.

win32com's dynamic binding resolves a parameterless method to its value on
attribute access, so call sites have to cope with getting either a value or an
unresolved bound method. The naive fix -- ``if callable(x): x()`` -- is wrong,
because a returned COM object is *itself* callable via its default member.
Invoking it silently yields the wrong thing, and in a linked-list walk it means
the chain never advances.

``com_get`` distinguishes the two by checking for ``_oleobj_``, which win32com
sets on COM objects and never on a plain bound method.
"""

from solidworks_mcp.automation.documents import DocumentOperations
from solidworks_mcp.constants import Defaults, SwErrors
from solidworks_mcp.utils.com import com_get


class _ComObject:
    """Mimics a win32com COM object: callable, and marked with _oleobj_."""

    _oleobj_ = object()

    def __init__(self, **attrs):
        self.__dict__.update(attrs)

    def __call__(self, *args, **kwargs):
        raise AssertionError(
            "default member invoked: com_get must not call a COM object"
        )


class _UnresolvedMethod:
    """Mimics the other binding, where the name stays a callable method."""

    def __init__(self, value):
        self._value = value

    def __call__(self):
        return self._value


class TestComGet:
    def test_returns_a_plain_value_untouched(self):
        assert com_get(_ComObject(Title="Part1"), "Title") == "Part1"

    def test_calls_an_unresolved_bound_method(self):
        obj = _ComObject(Title=_UnresolvedMethod("Part1"))

        assert com_get(obj, "Title") == "Part1"

    def test_does_not_invoke_a_returned_com_object(self):
        child = _ComObject(Title="Child")
        obj = _ComObject(Next=child)

        assert com_get(obj, "Next") is child

    def test_returns_none_when_the_chain_ends(self):
        assert com_get(_ComObject(Next=None), "Next") is None


# --- The document walk over a realistic COM chain ---

def _result(success, message, error_code=SwErrors.swSuccess, data=None):
    result = {"success": success, "message": message, "error_code": int(error_code)}
    if data:
        result["data"] = data
    return result


class _Documents(DocumentOperations):
    is_connected = True

    def __init__(self, sw_app):
        self._sw_app = sw_app

    _result = staticmethod(_result)


def _com_doc_chain(titles):
    """Build a COM-like linked list of open documents, newest first."""
    nxt = None
    for title in reversed(titles):
        nxt = _ComObject(GetTitle=title, GetType=1, GetNext=nxt)
    return nxt


class TestListOpenDocumentsOverComChain:
    def test_walks_the_whole_chain_exactly_once(self):
        sw_app = _ComObject(GetFirstDocument=_com_doc_chain(["A", "B", "C"]))

        result = _Documents(sw_app).list_open_documents()

        assert result["success"] is True
        assert [d["title"] for d in result["data"]["documents"]] == ["A", "B", "C"]

    def test_maps_document_types(self):
        doc = _ComObject(GetTitle="Asm1", GetType=2, GetNext=None)
        sw_app = _ComObject(GetFirstDocument=doc)

        result = _Documents(sw_app).list_open_documents()

        assert result["data"]["documents"][0]["type"] == "Assembly"

    def test_no_open_documents(self):
        sw_app = _ComObject(GetFirstDocument=None)

        result = _Documents(sw_app).list_open_documents()

        assert result["success"] is True
        assert result["data"]["documents"] == []

    def test_does_not_run_away_on_a_cyclic_chain(self):
        doc = _ComObject(GetTitle="A", GetType=1)
        doc.GetNext = doc  # a cycle: the walk must still terminate

        result = _Documents(_ComObject(GetFirstDocument=doc)).list_open_documents()

        assert len(result["data"]["documents"]) == Defaults.MAX_TREE_WALK
