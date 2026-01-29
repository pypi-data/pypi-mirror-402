"""
Unit tests for Storage class.
"""
import pytest

from cpg2py._abc import Storage


@pytest.mark.unit
class TestStorage:
    """Test cases for Storage class."""

    def test_storage_init_creates_empty_graph(self, storage):
        """
        Tests that Storage initialization creates an empty graph.

        Arrange: Create a new Storage instance
        Act: Check initial state
        Assert: Graph has no nodes or edges
        """
        assert storage is not None
        assert len(list(storage.get_nodes())) == 0
        assert len(list(storage.get_edges())) == 0

    def test_storage_add_node_adds_new_node(self, storage):
        """
        Tests that adding a new node succeeds.

        Arrange: Empty storage
        Act: Add a node
        Assert: Node is added and exists
        """
        result = storage.add_node("node1")
        assert result is True
        assert storage.contains_node("node1") is True

    def test_storage_add_node_duplicate_returns_false(self, storage):
        """
        Tests that adding a duplicate node returns False.

        Arrange: Storage with existing node
        Act: Add the same node again
        Assert: Returns False, node count unchanged
        """
        storage.add_node("node1")
        result = storage.add_node("node1")
        assert result is False
        assert len(list(storage.get_nodes())) == 1

    def test_storage_add_node_multiple_adds_all_nodes(self, storage):
        """
        Tests that multiple nodes can be added.

        Arrange: Empty storage
        Act: Add multiple nodes
        Assert: All nodes are added
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        assert len(list(storage.get_nodes())) == 3

    def test_storage_contains_node_returns_true_for_existing(self, storage):
        """
        Tests that contains_node returns True for existing nodes.

        Arrange: Storage with a node
        Act: Check if node exists
        Assert: Returns True
        """
        storage.add_node("node1")
        assert storage.contains_node("node1") is True

    def test_storage_contains_node_returns_false_for_missing(self, storage):
        """
        Tests that contains_node returns False for missing nodes.

        Arrange: Empty storage
        Act: Check if non-existent node exists
        Assert: Returns False
        """
        assert storage.contains_node("node1") is False

    def test_storage_add_edge_adds_new_edge(self, storage):
        """
        Tests that adding a new edge succeeds.

        Arrange: Storage with source and target nodes
        Act: Add an edge
        Assert: Edge is added and exists
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "EDGE_TYPE")
        result = storage.add_edge(edge_id)
        assert result is True
        assert storage.contains_edge(edge_id) is True

    def test_storage_add_edge_duplicate_returns_false(self, storage):
        """
        Tests that adding a duplicate edge returns False.

        Arrange: Storage with existing edge
        Act: Add the same edge again
        Assert: Returns False
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "EDGE_TYPE")
        storage.add_edge(edge_id)
        result = storage.add_edge(edge_id)
        assert result is False

    def test_storage_add_edge_missing_source_returns_false(self, storage):
        """
        Tests that adding edge with missing source node returns False.

        Arrange: Storage without source node
        Act: Add edge with missing source
        Assert: Returns False
        """
        storage.add_node("node2")
        edge_id = ("node1", "node2", "EDGE_TYPE")
        result = storage.add_edge(edge_id)
        assert result is False

    def test_storage_add_edge_missing_target_returns_false(self, storage):
        """
        Tests that adding edge with missing target node returns False.

        Arrange: Storage without target node
        Act: Add edge with missing target
        Assert: Returns False
        """
        storage.add_node("node1")
        edge_id = ("node1", "node2", "EDGE_TYPE")
        result = storage.add_edge(edge_id)
        assert result is False

    def test_storage_out_edges_returns_all_outgoing_edges(self, storage):
        """
        Tests that out_edges returns all outgoing edges for a node.

        Arrange: Storage with multiple outgoing edges
        Act: Get outgoing edges
        Assert: All outgoing edges are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        edge1 = ("node1", "node2", "TYPE1")
        edge2 = ("node1", "node3", "TYPE2")
        storage.add_edge(edge1)
        storage.add_edge(edge2)
        out_edges = list(storage.out_edges("node1"))
        assert len(out_edges) == 2
        assert edge1 in out_edges
        assert edge2 in out_edges

    def test_storage_in_edges_returns_all_incoming_edges(self, storage):
        """
        Tests that in_edges returns all incoming edges for a node.

        Arrange: Storage with multiple incoming edges
        Act: Get incoming edges
        Assert: All incoming edges are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        edge1 = ("node1", "node2", "TYPE1")
        edge2 = ("node3", "node2", "TYPE2")
        storage.add_edge(edge1)
        storage.add_edge(edge2)
        in_edges = list(storage.in_edges("node2"))
        assert len(in_edges) == 2
        assert edge1 in in_edges
        assert edge2 in in_edges

    def test_storage_successors_returns_all_successor_nodes(self, storage):
        """
        Tests that successors returns all successor nodes.

        Arrange: Storage with multiple successors
        Act: Get successors
        Assert: All successor nodes are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        storage.add_edge(("node1", "node2", "TYPE1"))
        storage.add_edge(("node1", "node3", "TYPE2"))
        successors = list(storage.successors("node1"))
        assert len(successors) == 2
        assert "node2" in successors
        assert "node3" in successors

    def test_storage_predecessors_returns_all_predecessor_nodes(self, storage):
        """
        Tests that predecessors returns all predecessor nodes.

        Arrange: Storage with multiple predecessors
        Act: Get predecessors
        Assert: All predecessor nodes are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        storage.add_node("node3")
        storage.add_edge(("node1", "node2", "TYPE1"))
        storage.add_edge(("node3", "node2", "TYPE2"))
        predecessors = list(storage.predecessors("node2"))
        assert len(predecessors) == 2
        assert "node1" in predecessors
        assert "node3" in predecessors

    def test_storage_set_node_props_sets_properties(self, storage):
        """
        Tests that set_node_props sets node properties.

        Arrange: Storage with a node
        Act: Set node properties
        Assert: Properties are set correctly
        """
        storage.add_node("node1")
        props = {"name": "test", "type": "AST"}
        result = storage.set_node_props("node1", props)
        assert result is True
        node_props = storage.get_node_props("node1")
        assert node_props["name"] == "test"
        assert node_props["type"] == "AST"

    def test_storage_set_node_props_nonexistent_returns_false(self, storage):
        """
        Tests that set_node_props returns False for nonexistent node.

        Arrange: Empty storage
        Act: Set properties for non-existent node
        Assert: Returns False
        """
        props = {"name": "test"}
        result = storage.set_node_props("node1", props)
        assert result is False

    def test_storage_get_node_props_returns_properties(self, storage):
        """
        Tests that get_node_props returns node properties.

        Arrange: Storage with node and properties
        Act: Get node properties
        Assert: Properties are returned correctly
        """
        storage.add_node("node1")
        props = {"name": "test", "type": "AST"}
        storage.set_node_props("node1", props)
        retrieved_props = storage.get_node_props("node1")
        assert retrieved_props is not None
        assert retrieved_props["name"] == "test"

    def test_storage_get_node_props_nonexistent_returns_none(self, storage):
        """
        Tests that get_node_props returns None for nonexistent node.

        Arrange: Empty storage
        Act: Get properties for non-existent node
        Assert: Returns None
        """
        props = storage.get_node_props("node1")
        assert props is None

    def test_storage_set_node_prop_sets_single_property(self, storage):
        """
        Tests that set_node_prop sets a single property.

        Arrange: Storage with a node
        Act: Set single property
        Assert: Property is set correctly
        """
        storage.add_node("node1")
        result = storage.set_node_prop("node1", "name", "test")
        assert result is True
        value = storage.get_node_prop("node1", "name")
        assert value == "test"

    def test_storage_get_node_prop_returns_property_value(self, storage):
        """
        Tests that get_node_prop returns property value.

        Arrange: Storage with node and property
        Act: Get property value
        Assert: Correct value is returned
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "name", "test")
        value = storage.get_node_prop("node1", "name")
        assert value == "test"

    def test_storage_get_node_prop_nonexistent_returns_none(self, storage):
        """
        Tests that get_node_prop returns None for nonexistent property.

        Arrange: Empty storage
        Act: Get property from non-existent node
        Assert: Returns None
        """
        value = storage.get_node_prop("node1", "name")
        assert value is None

    def test_storage_set_edge_props_sets_properties(self, storage):
        """
        Tests that set_edge_props sets edge properties.

        Arrange: Storage with an edge
        Act: Set edge properties
        Assert: Properties are set correctly
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        props = {"weight": 1.0, "label": "test"}
        result = storage.set_edge_props(edge_id, props)
        assert result is True
        edge_props = storage.get_edge_props(edge_id)
        assert edge_props["weight"] == 1.0
        assert edge_props["label"] == "test"

    def test_storage_set_edge_props_nonexistent_returns_false(self, storage):
        """
        Tests that set_edge_props returns False for nonexistent edge.

        Arrange: Empty storage
        Act: Set properties for non-existent edge
        Assert: Returns False
        """
        props = {"weight": 1.0}
        edge_id = ("node1", "node2", "TYPE")
        result = storage.set_edge_props(edge_id, props)
        assert result is False

    def test_storage_get_edge_props_returns_properties(self, storage):
        """
        Tests that get_edge_props returns edge properties.

        Arrange: Storage with edge and properties
        Act: Get edge properties
        Assert: Properties are returned correctly
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        props = {"weight": 1.0}
        storage.set_edge_props(edge_id, props)
        retrieved_props = storage.get_edge_props(edge_id)
        assert retrieved_props is not None
        assert retrieved_props["weight"] == 1.0

    def test_storage_set_edge_prop_sets_single_property(self, storage):
        """
        Tests that set_edge_prop sets a single property.

        Arrange: Storage with an edge
        Act: Set single property
        Assert: Property is set correctly
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        result = storage.set_edge_prop(edge_id, "weight", 1.0)
        assert result is True
        value = storage.get_edge_prop(edge_id, "weight")
        assert value == 1.0

    def test_storage_get_edge_prop_returns_property_value(self, storage):
        """
        Tests that get_edge_prop returns property value.

        Arrange: Storage with edge and property
        Act: Get property value
        Assert: Correct value is returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "weight", 1.0)
        value = storage.get_edge_prop(edge_id, "weight")
        assert value == 1.0

    def test_storage_remove_node_removes_node(self, storage):
        """
        Tests that remove_node removes a node.

        Arrange: Storage with a node
        Act: Remove node
        Assert: Node is removed
        """
        storage.add_node("node1")
        result = storage.remove_node("node1")
        assert result is True
        assert storage.contains_node("node1") is False

    def test_storage_remove_node_nonexistent_returns_false(self, storage):
        """
        Tests that remove_node returns False for nonexistent node.

        Arrange: Empty storage
        Act: Remove non-existent node
        Assert: Returns False
        """
        result = storage.remove_node("node1")
        assert result is False

    def test_storage_remove_edge_removes_edge(self, storage):
        """
        Tests that remove_edge removes an edge.

        Arrange: Storage with an edge
        Act: Remove edge
        Assert: Edge is removed
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        result = storage.remove_edge(edge_id)
        assert result is True
        assert storage.contains_edge(edge_id) is False

    def test_storage_remove_edge_nonexistent_returns_false(self, storage):
        """
        Tests that remove_edge returns False for nonexistent edge.

        Arrange: Empty storage
        Act: Remove non-existent edge
        Assert: Returns False
        """
        edge_id = ("node1", "node2", "TYPE")
        result = storage.remove_edge(edge_id)
        assert result is False

    def test_storage_get_nodes_returns_all_nodes(self, storage):
        """
        Tests that get_nodes returns all nodes.

        Arrange: Storage with multiple nodes
        Act: Get all nodes
        Assert: All nodes are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        nodes = list(storage.get_nodes())
        assert len(nodes) == 2
        assert "node1" in nodes
        assert "node2" in nodes

    def test_storage_get_edges_returns_all_edges(self, storage):
        """
        Tests that get_edges returns all edges.

        Arrange: Storage with an edge
        Act: Get all edges
        Assert: All edges are returned
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        edges = list(storage.get_edges())
        assert len(edges) == 1
        assert edge_id in edges
