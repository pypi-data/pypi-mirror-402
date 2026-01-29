from __future__ import annotations

import functools
from typing import Callable, Iterable, Optional

from .._abc import AbcGraphQuerier, Storage
from .._exceptions import EdgeNotFoundError, NodeNotFoundError, TopFileNotFoundError
from .._logger import get_logger
from .edge import CpgEdge
from .node import CpgNode

logger = get_logger(__name__)


class CpgGraph(AbcGraphQuerier[CpgNode, CpgEdge]):
    """
    Graph implementation for Object Property Diagram (OPG) used by ODgen and FAST.

    Provides concrete implementation of graph query operations for CPG data.

    This class is parameterized with CpgNode and CpgEdge types, ensuring type safety
    throughout the graph operations.
    """

    __EdgeCondition = Callable[[CpgEdge], bool]
    __always_true = lambda _: True

    def __init__(self, target: Storage) -> None:
        super().__init__(target)

    def node(self, whose_id_is: str) -> Optional[CpgNode]:
        """
        Returns a node by its ID.

        Args:
            whose_id_is: Node ID to look up

        Returns:
            Node instance if found

        Raises:
            NodeNotFoundError: If node is not found in the graph
        """
        try:
            return CpgNode(self.storage, whose_id_is)
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.exception("Unexpected error while finding node with id %s", whose_id_is)
            raise NodeNotFoundError(whose_id_is) from e

    def edge(self, fid: str, tid: str, eid: str) -> Optional[CpgEdge]:
        """
        Returns an edge by its source, target, and edge type.

        Args:
            fid: Source node ID
            tid: Target node ID
            eid: Edge type/ID

        Returns:
            Edge instance if found

        Raises:
            EdgeNotFoundError: If edge is not found in the graph
        """
        try:
            return CpgEdge(self.storage, fid, tid, eid)
        except EdgeNotFoundError:
            raise
        except Exception as e:
            logger.exception(
                "Unexpected error while finding edge from %s to %s, eid is %s", fid, tid, eid
            )
            raise EdgeNotFoundError(fid, tid, str(eid)) from e

    @functools.lru_cache()
    def topfile_node(self, of_nid: str) -> CpgNode:
        """
        Finds the top file node from the input node.

        Args:
            of_nid: Starting node ID

        Returns:
            Top file node

        Raises:
            TopFileNotFoundError: If top file node cannot be found
            NodeNotFoundError: If starting node is not found
        """
        of_node = self.node(of_nid)
        if of_node.type == "File":
            return of_node
        if "TOPLEVEL_FILE" in of_node.flags:
            return of_node
        parents = self.prev(of_node, lambda e: e.type in ["PARENT_OF", "ENTRY", "EXIT"])
        for pre in parents:
            try:
                top_file = self.topfile_node(pre.id)
                return top_file
            except TopFileNotFoundError:
                continue
        logger.error("Cannot find top file node from node %s", of_nid)
        raise TopFileNotFoundError(of_nid)

    def succ(self, of: CpgNode, who_satisifies: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns successor nodes connected to the input node.

        Args:
            of: Source node
            who_satisifies: Optional edge condition filter

        Yields:
            Successor nodes matching the condition
        """
        return super().succ(of, who_satisifies)

    def prev(self, of: CpgNode, who_satisifies: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns predecessor nodes connected to the input node.

        Args:
            of: Target node
            who_satisifies: Optional edge condition filter

        Yields:
            Predecessor nodes matching the condition
        """
        return super().prev(of, who_satisifies)

    def children(self, of: CpgNode, extra: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns child nodes connected via PARENT_OF edges.

        Args:
            of: Parent node
            extra: Additional edge condition filter

        Returns:
            Iterable of child nodes
        """
        return self.succ(of, lambda e: extra(e) and (e.type == "PARENT_OF"))

    def parent(self, of: CpgNode, extra: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns parent nodes connected via PARENT_OF edges.

        Args:
            of: Child node
            extra: Additional edge condition filter

        Returns:
            Iterable of parent nodes
        """
        return self.prev(of, lambda e: extra(e) and (e.type == "PARENT_OF"))

    def flow_to(self, of: CpgNode, extra: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns successor nodes connected via FLOWS_TO edges.

        Args:
            of: Source node
            extra: Additional edge condition filter

        Returns:
            Iterable of flow successor nodes
        """
        return self.succ(of, lambda e: extra(e) and (e.type == "FLOWS_TO"))

    def flow_from(self, of: CpgNode, extra: __EdgeCondition = __always_true) -> Iterable[CpgNode]:
        """
        Returns predecessor nodes connected via FLOWS_TO edges.

        Args:
            of: Target node
            extra: Additional edge condition filter

        Returns:
            Iterable of flow predecessor nodes
        """
        return self.prev(of, lambda e: extra(e) and (e.type == "FLOWS_TO"))
