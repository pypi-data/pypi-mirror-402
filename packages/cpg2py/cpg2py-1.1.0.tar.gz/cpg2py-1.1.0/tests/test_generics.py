"""
Unit tests for generic type functionality.
"""
import pytest
from typing import get_args, get_origin

from cpg2py._abc import AbcGraphQuerier, Storage
from cpg2py._cpg import CpgEdge, CpgGraph, CpgNode


@pytest.mark.unit
class TestGenerics:
    """Test cases for generic type functionality."""

    def test_graph_is_generic_subclass(self, storage):
        """
        Tests that CpgGraph is a generic subclass of AbcGraphQuerier.

        Arrange: Storage instance
        Act: Create Graph and check type
        Assert: Graph is instance of generic AbcGraphQuerier
        """
        graph = CpgGraph(storage)
        assert isinstance(graph, AbcGraphQuerier)
        assert isinstance(graph, CpgGraph)

    def test_graph_node_returns_concrete_node_type(self, graph, storage):
        """
        Tests that graph.node returns CpgNode type (not just AbcNodeQuerier).

        Arrange: Storage with a node
        Act: Get node and check type
        Assert: Returns CpgNode instance
        """
        storage.add_node("node1")
        node = graph.node("node1")
        assert node is not None
        assert isinstance(node, CpgNode)
        assert isinstance(node, type(node))  # Type consistency

    def test_graph_edge_returns_concrete_edge_type(self, graph, storage):
        """
        Tests that graph.edge returns CpgEdge type (not just AbcEdgeQuerier).

        Arrange: Storage with nodes and edge
        Act: Get edge and check type
        Assert: Returns CpgEdge instance
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_edge(("node1", "node2", "TYPE"))
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge is not None
        assert isinstance(edge, CpgEdge)

    def test_graph_succ_returns_concrete_node_types(self, graph, storage):
        """
        Tests that graph.succ returns Iterable[CpgNode] with correct types.

        Arrange: Storage with nodes and edges
        Act: Get successors and check types
        Assert: All successors are CpgNode instances
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        storage.add_edge(("node1", "node2", "TYPE1"))
        storage.add_edge(("node1", "node3", "TYPE2"))
        node1 = graph.node("node1")
        successors = list(graph.succ(node1))
        assert len(successors) == 2
        for succ in successors:
            assert isinstance(succ, CpgNode)
            assert hasattr(succ, "code")  # CpgNode-specific property

    def test_graph_prev_returns_concrete_node_types(self, graph, storage):
        """
        Tests that graph.prev returns Iterable[CpgNode] with correct types.

        Arrange: Storage with nodes and edges
        Act: Get predecessors and check types
        Assert: All predecessors are CpgNode instances
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        storage.add_edge(("node1", "node2", "TYPE1"))
        storage.add_edge(("node3", "node2", "TYPE2"))
        node2 = graph.node("node2")
        predecessors = list(graph.prev(node2))
        assert len(predecessors) == 2
        for pred in predecessors:
            assert isinstance(pred, CpgNode)
            assert hasattr(pred, "code")  # CpgNode-specific property

    def test_graph_nodes_returns_concrete_node_types(self, graph, storage):
        """
        Tests that graph.nodes returns Iterable[CpgNode] with correct types.

        Arrange: Storage with multiple nodes
        Act: Get all nodes and check types
        Assert: All nodes are CpgNode instances
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        nodes = list(graph.nodes())
        assert len(nodes) == 3
        for node in nodes:
            assert isinstance(node, CpgNode)
            assert hasattr(node, "code")  # CpgNode-specific property

    def test_graph_edges_returns_concrete_edge_types(self, graph, storage):
        """
        Tests that graph.edges returns Iterable[CpgEdge] with correct types.

        Arrange: Storage with edges
        Act: Get all edges and check types
        Assert: All edges are CpgEdge instances
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        storage.add_edge(("node1", "node2", "TYPE1"))
        storage.add_edge(("node2", "node3", "TYPE2"))
        edges = list(graph.edges())
        assert len(edges) == 2
        for edge in edges:
            assert isinstance(edge, CpgEdge)
            assert hasattr(edge, "type")  # CpgEdge-specific property

    def test_graph_descendants_returns_concrete_node_types(self, graph, storage):
        """
        Tests that graph.descendants returns Iterable[CpgNode] with correct types.

        Arrange: Storage with hierarchical structure
        Act: Get descendants and check types
        Assert: All descendants are CpgNode instances
        """
        storage.add_node("root")
        storage.add_node("child1")
        storage.add_node("child2")
        storage.add_node("grandchild")
        storage.add_edge(("root", "child1", "PARENT_OF"))
        storage.add_edge(("root", "child2", "PARENT_OF"))
        storage.add_edge(("child1", "grandchild", "PARENT_OF"))
        root = graph.node("root")
        descendants = list(graph.descendants(root))
        assert len(descendants) >= 2
        for desc in descendants:
            assert isinstance(desc, CpgNode)

    def test_graph_ancestors_returns_concrete_node_types(self, graph, storage):
        """
        Tests that graph.ancestors returns Iterable[CpgNode] with correct types.

        Arrange: Storage with hierarchical structure
        Act: Get ancestors and check types
        Assert: All ancestors are CpgNode instances
        """
        storage.add_node("root")
        storage.add_node("child1")
        storage.add_node("grandchild")
        storage.add_edge(("root", "child1", "PARENT_OF"))
        storage.add_edge(("child1", "grandchild", "PARENT_OF"))
        grandchild = graph.node("grandchild")
        ancestors = list(graph.ancestors(grandchild))
        assert len(ancestors) >= 1
        for anc in ancestors:
            assert isinstance(anc, CpgNode)

    def test_graph_first_node_returns_concrete_node_type(self, graph, storage):
        """
        Tests that graph.first_node returns CpgNode type.

        Arrange: Storage with nodes
        Act: Get first node and check type
        Assert: Returns CpgNode instance or None
        """
        storage.add_node("node1")
        storage.add_node("node2")
        first_node = graph.first_node()
        assert first_node is not None
        assert isinstance(first_node, CpgNode)

    def test_graph_first_node_returns_none_when_empty(self, graph):
        """
        Tests that graph.first_node returns None when graph is empty.

        Arrange: Empty graph
        Act: Get first node
        Assert: Returns None
        """
        first_node = graph.first_node()
        assert first_node is None
