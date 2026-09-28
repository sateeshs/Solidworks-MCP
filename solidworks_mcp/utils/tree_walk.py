"""Iteration bounds for SolidWorks COM linked-list traversals.

SolidWorks exposes feature trees, open documents and mate chains as linked
lists: take a first node, then follow ``GetNextFeature`` / ``GetNext`` /
``GetNextSubFeature`` until it yields nothing. A naive loop over one of those
never terminates if the chain is cyclic or malformed, and each iteration holds
on to another COM proxy -- so the process grows without bound instead of
raising. Every traversal is therefore capped.

Call :func:`walk_exhausted` at the top of the loop body and ``break`` when it
returns True. The caller keeps its own termination condition, so live
SolidWorks behaviour is unchanged for well-formed chains.
"""

import logging

from ..constants import Defaults

logger = logging.getLogger(__name__)


def walk_exhausted(
    count: int,
    what: str,
    limit: int = Defaults.MAX_TREE_WALK,
) -> bool:
    """Report whether a traversal has used up its safe iteration budget.

    Args:
        count: Number of nodes visited so far.
        what: What is being walked, for the log message (e.g. "feature tree").
        limit: Maximum nodes to visit before giving up.

    Returns:
        True when the budget is spent and the caller must stop iterating.
    """
    if count < limit:
        return False

    logger.warning(
        "Aborting %s traversal after %d nodes: the chain is cyclic, malformed, "
        "or a test double. Results are truncated.",
        what,
        limit,
    )
    return True
