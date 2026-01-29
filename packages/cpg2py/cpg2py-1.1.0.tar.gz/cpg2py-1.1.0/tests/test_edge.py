"""
Unit tests for Edge class.
"""
import pytest

from cpg2py._abc import Storage
from cpg2py._cpg import CpgGraph


@pytest.mark.unit
class TestEdge:
    """Test cases for Edge class."""

    def test_edge_id_returns_edge_tuple(self, graph, storage):
        """
        Tests that edge.id returns the edge tuple.

        Arrange: Storage with nodes and edge
        Act: Get edge and access id property
        Assert: Returns correct edge tuple
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.id == edge_id

    def test_edge_start_returns_integer_with_primary_key(self, graph, storage):
        """
        Tests that edge.start returns integer using primary key.

        Arrange: Storage with edge and start property
        Act: Get edge and access start property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "start", "1")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.start == 1

    def test_edge_start_returns_integer_with_alternative_key(self, graph, storage):
        """
        Tests that edge.start returns integer using alternative key.

        Arrange: Storage with edge and start:START_ID property
        Act: Get edge and access start property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "start:START_ID", "1")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.start == 1

    def test_edge_end_returns_integer_with_primary_key(self, graph, storage):
        """
        Tests that edge.end returns integer using primary key.

        Arrange: Storage with edge and end property
        Act: Get edge and access end property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "end", "2")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.end == 2

    def test_edge_end_returns_integer_with_alternative_key(self, graph, storage):
        """
        Tests that edge.end returns integer using alternative key.

        Arrange: Storage with edge and end:END_ID property
        Act: Get edge and access end property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "end:END_ID", "2")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.end == 2

    def test_edge_type_returns_string_with_primary_key(self, graph, storage):
        """
        Tests that edge.type returns string using primary key.

        Arrange: Storage with edge and type property
        Act: Get edge and access type property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "type", "PARENT_OF")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.type == "PARENT_OF"

    def test_edge_type_returns_string_with_alternative_key(self, graph, storage):
        """
        Tests that edge.type returns string using alternative key.

        Arrange: Storage with edge and type:TYPE property
        Act: Get edge and access type property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "type:TYPE", "PARENT_OF")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.type == "PARENT_OF"

    def test_edge_var_returns_string(self, graph, storage):
        """
        Tests that edge.var returns string.

        Arrange: Storage with edge and var property
        Act: Get edge and access var property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.add_node("node2")
        edge_id = ("node1", "node2", "TYPE")
        storage.add_edge(edge_id)
        storage.set_edge_prop(edge_id, "var", "variable_name")
        edge = graph.edge("node1", "node2", "TYPE")
        assert edge.var == "variable_name"
