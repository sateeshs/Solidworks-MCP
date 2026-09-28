"""Safe attribute access on SolidWorks COM objects.

win32com's dynamic binding is inconsistent about parameterless members: some
resolve to their value on attribute access, others stay an unresolved bound
method that still needs calling. Code therefore has to handle both.

The obvious guard is wrong::

    value = obj.GetNext
    if callable(value):      # a COM object is callable too!
        value = value()

A COM object exposes a default member, which makes it callable. Invoking it
returns the default member's value rather than the object, so a linked-list
walk written this way never advances -- it spins on the same node forever.

``com_get`` tells the two apart by checking for ``_oleobj_``, which win32com
sets on COM objects and never on a plain bound method.
"""

from typing import Any


def com_get(obj: Any, name: str) -> Any:
    """Read a parameterless COM method or property.

    Args:
        obj: The COM object to read from.
        name: Member name, e.g. ``"GetNext"``.

    Returns:
        The member's value, calling it only when it is a plain Python callable
        (an unresolved bound method) and not a COM object.
    """
    value = getattr(obj, name)
    if callable(value) and not hasattr(value, "_oleobj_"):  # not a COM object
        value = value()
    return value
