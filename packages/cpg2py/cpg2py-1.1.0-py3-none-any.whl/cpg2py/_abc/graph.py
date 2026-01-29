from __future__ import annotations

import abc
from collections import deque
from typing import Callable, Deque, Generic, Iterable, List, Optional, TypeVar

from .edge import AbcEdgeQuerier
from .node import AbcNodeQuerier
from .storage import Storage

# Type variables for generic graph querier
# Covariant: subtypes can be used where base types are expected
_NodeType = TypeVar("_NodeType", bound=AbcNodeQuerier, covariant=True)
_EdgeType = TypeVar("_EdgeType", bound=AbcEdgeQuerier, covariant=True)

# Type variables for concrete implementations (invariant)
_ConcreteNodeType = TypeVar("_ConcreteNodeType", bound=AbcNodeQuerier)
_ConcreteEdgeType = TypeVar("_ConcreteEdgeType", bound=AbcEdgeQuerier)


class AbcGraphQuerier(abc.ABC, Generic[_ConcreteNodeType, _ConcreteEdgeType]):
    """
    Abstract base class for graph query operations.

    Provides interface for querying nodes, edges, and traversing graph structures.

    This is a generic class that allows type-safe operations based on the concrete
    node and edge types. When you create a concrete implementation, specify the
    node and edge types:

    Example:
        class MyGraph(AbcGraphQuerier[MyNode, MyEdge]):
            ...

    Type Parameters:
        _ConcreteNodeType: The concrete node type returned by node() and related methods
        _ConcreteEdgeType: The concrete edge type returned by edge() and used in conditions
    """

    __NodeCondition = Callable[[_NodeType], bool]
    __EdgeCondition = Callable[[_EdgeType], bool]

    __always_true = lambda _: True

    __NodesResult = Iterable[_ConcreteNodeType]
    __EdgesResult = Iterable[_ConcreteEdgeType]

    def __init__(self, target: Storage, maxdepth: int = -1) -> None:
        """
        Initializes a graph querier.

        Args:
            target: Storage instance containing the graph
            maxdepth: Maximum depth for traversal operations (-1 for unlimited)
        """
        self.__graph: Storage = target
        self.__maxdepth: int = maxdepth

    @property
    def storage(self) -> Storage:
        """
        Returns the underlying storage instance.

        Returns:
            Storage instance
        """
        return self.__graph

    @abc.abstractmethod
    def node(self, whose_id_is: str) -> Optional[_ConcreteNodeType]:
        """
        Returns a node by its ID.

        Args:
            whose_id_is: Node ID to look up

        Returns:
            Node instance if found, None otherwise
        """
        raise NotImplementedError

    @abc.abstractmethod
    def edge(self, fid: str, tid: str, eid: str) -> Optional[_ConcreteEdgeType]:
        """
        Returns an edge by its source, target, and edge type.

        Args:
            fid: Source node ID
            tid: Target node ID
            eid: Edge type/ID

        Returns:
            Edge instance if found, None otherwise
        """
        raise NotImplementedError

    def nodes(
        self, who_satisifies: __NodeCondition = __always_true
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns all nodes matching the condition.

        Args:
            who_satisifies: Node condition filter

        Yields:
            Nodes matching the condition
        """
        for nid in self.__graph.get_nodes():
            cur_node = self.node(whose_id_is=nid)
            if cur_node and who_satisifies(cur_node):
                yield cur_node

    def first_node(
        self, who_satisifies: __NodeCondition = __always_true
    ) -> Optional[_ConcreteNodeType]:
        """
        Returns the first node matching the condition.

        Args:
            who_satisifies: Node condition filter

        Returns:
            First matching node, or None if no match
        """
        return next(self.nodes(who_satisifies), None)

    def edges(
        self, who_satisifies: __EdgeCondition = __always_true
    ) -> Iterable[_ConcreteEdgeType]:
        """
        Returns all edges matching the condition.

        Args:
            who_satisifies: Edge condition filter

        Yields:
            Edges matching the condition
        """
        for from_id, to_id, edge_id in self.__graph.get_edges():
            cur_edge = self.edge(from_id, to_id, edge_id)
            if cur_edge and who_satisifies(cur_edge):
                yield cur_edge

    def succ(
        self, of: _ConcreteNodeType, who_satisifies: __EdgeCondition = __always_true
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns successor nodes connected to the input node.

        Args:
            of: Source node
            who_satisifies: Edge condition filter

        Yields:
            Successor nodes matching the condition
        """
        for src, dst, edge_type in self.__graph.out_edges(of.node_id):
            edge = self.edge(src, dst, edge_type)
            if edge and who_satisifies(edge):
                node = self.node(whose_id_is=dst)
                if node:
                    yield node

    def prev(
        self, of: _ConcreteNodeType, who_satisifies: __EdgeCondition = __always_true
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns predecessor nodes connected to the input node.

        Args:
            of: Target node
            who_satisifies: Edge condition filter

        Yields:
            Predecessor nodes matching the condition
        """
        for src, dst, edge_type in self.__graph.in_edges(of.node_id):
            edge = self.edge(src, dst, edge_type)
            if edge and who_satisifies(edge):
                node = self.node(whose_id_is=src)
                if node:
                    yield node

    def __bfs_search(
        self, root: _ConcreteNodeType, condition: __EdgeCondition, reverse: bool
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns nodes from src node by BFS order (src node not included).

        Args:
            root: Starting node
            condition: Edge condition filter
            reverse: If True, traverse backwards

        Yields:
            Nodes in BFS order (excluding root)
        """
        if root is None:
            return
        visited_nids: List[str] = []
        nodes_queue: Deque[_ConcreteNodeType] = deque([root, None])
        depth = self.__maxdepth
        while depth != 0 and len(nodes_queue) > 1:
            cur_node = nodes_queue.popleft()
            if cur_node is None:
                nodes_queue.append(None)
                depth -= 1
            elif cur_node.node_id not in visited_nids:
                visited_nids.append(cur_node.node_id)
                if not reverse:
                    n_nodes = self.succ(cur_node, condition)
                else:
                    n_nodes = self.prev(cur_node, condition)
                nodes_queue.extend(n_nodes)
                if root.node_id != cur_node.node_id:
                    yield cur_node

    def descendants(
        self, src: _ConcreteNodeType, condition: __EdgeCondition = __always_true
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns descendants from src node by BFS order (src node not included).

        Args:
            src: Source node
            condition: Edge condition filter

        Yields:
            Descendant nodes in BFS order
        """
        return self.__bfs_search(src, condition, reverse=False)

    def ancestors(
        self, src: _ConcreteNodeType, condition: __EdgeCondition = __always_true
    ) -> Iterable[_ConcreteNodeType]:
        """
        Returns ancestors from src node by BFS order (src node not included).

        Args:
            src: Source node
            condition: Edge condition filter

        Yields:
            Ancestor nodes in BFS order
        """
        return self.__bfs_search(src, condition, reverse=True)
