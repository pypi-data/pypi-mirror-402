"""
Unit tests for Node class.
"""
import pytest

from cpg2py._abc import Storage
from cpg2py._cpg import CpgGraph


@pytest.mark.unit
class TestNode:
    """Test cases for Node class."""

    def test_node_id_returns_node_identifier(self, graph, storage):
        """
        Tests that node.id returns the node identifier.

        Arrange: Storage with a node
        Act: Get node and access id property
        Assert: Returns correct node ID
        """
        storage.add_node("node1")
        node = graph.node("node1")
        assert node.id == "node1"

    def test_node_code_returns_code_property(self, graph, storage):
        """
        Tests that node.code returns the code property.

        Arrange: Storage with node and code property
        Act: Get node and access code property
        Assert: Returns correct code value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "code", "test code")
        node = graph.node("node1")
        assert node.code == "test code"

    def test_node_label_returns_label_with_primary_key(self, graph, storage):
        """
        Tests that node.label returns label using primary key.

        Arrange: Storage with node and labels:label property
        Act: Get node and access label property
        Assert: Returns correct label value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "labels:label", "test_label")
        node = graph.node("node1")
        assert node.label == "test_label"

    def test_node_label_returns_label_with_alternative_key(self, graph, storage):
        """
        Tests that node.label returns label using alternative key.

        Arrange: Storage with node and labels property
        Act: Get node and access label property
        Assert: Returns correct label value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "labels", "test_label")
        node = graph.node("node1")
        assert node.label == "test_label"

    def test_node_flags_returns_list_of_flags(self, graph, storage):
        """
        Tests that node.flags returns a list of flags.

        Arrange: Storage with node and flags property
        Act: Get node and access flags property
        Assert: Returns list with correct flags
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "flags", "FLAG1 FLAG2 FLAG3")
        node = graph.node("node1")
        assert len(node.flags) == 3
        assert "FLAG1" in node.flags
        assert "FLAG2" in node.flags
        assert "FLAG3" in node.flags

    def test_node_flags_returns_empty_list_when_missing(self, graph, storage):
        """
        Tests that node.flags returns empty list when no flags exist.

        Arrange: Storage with node without flags
        Act: Get node and access flags property
        Assert: Returns empty list
        """
        storage.add_node("node1")
        node = graph.node("node1")
        assert node.flags == []

    def test_node_line_num_returns_integer_with_primary_key(self, graph, storage):
        """
        Tests that node.line_num returns integer using primary key.

        Arrange: Storage with node and lineno:int property
        Act: Get node and access line_num property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "lineno:int", "42")
        node = graph.node("node1")
        assert node.line_num == 42

    def test_node_line_num_returns_integer_with_alternative_key(self, graph, storage):
        """
        Tests that node.line_num returns integer using alternative key.

        Arrange: Storage with node and lineno property
        Act: Get node and access line_num property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "lineno", "42")
        node = graph.node("node1")
        assert node.line_num == 42

    def test_node_line_num_returns_none_for_invalid_value(self, graph, storage):
        """
        Tests that node.line_num returns None for invalid value.

        Arrange: Storage with node and invalid lineno property
        Act: Get node and access line_num property
        Assert: Returns None
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "lineno", "invalid")
        node = graph.node("node1")
        assert node.line_num is None

    def test_node_children_num_returns_integer(self, graph, storage):
        """
        Tests that node.children_num returns integer.

        Arrange: Storage with node and childnum:int property
        Act: Get node and access children_num property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "childnum:int", "5")
        node = graph.node("node1")
        assert node.children_num == 5

    def test_node_func_id_returns_integer(self, graph, storage):
        """
        Tests that node.func_id returns integer.

        Arrange: Storage with node and funcid:int property
        Act: Get node and access func_id property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "funcid:int", "10")
        node = graph.node("node1")
        assert node.func_id == 10

    def test_node_class_name_returns_string(self, graph, storage):
        """
        Tests that node.class_name returns string.

        Arrange: Storage with node and classname property
        Act: Get node and access class_name property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "classname", "TestClass")
        node = graph.node("node1")
        assert node.class_name == "TestClass"

    def test_node_namespace_returns_string(self, graph, storage):
        """
        Tests that node.namespace returns string.

        Arrange: Storage with node and namespace property
        Act: Get node and access namespace property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "namespace", "com.example")
        node = graph.node("node1")
        assert node.namespace == "com.example"

    def test_node_name_returns_string(self, graph, storage):
        """
        Tests that node.name returns string.

        Arrange: Storage with node and name property
        Act: Get node and access name property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "name", "test_name")
        node = graph.node("node1")
        assert node.name == "test_name"

    def test_node_end_num_returns_integer_with_primary_key(self, graph, storage):
        """
        Tests that node.end_num returns integer using primary key.

        Arrange: Storage with node and endlineno:int property
        Act: Get node and access end_num property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "endlineno:int", "50")
        node = graph.node("node1")
        assert node.end_num == 50

    def test_node_end_num_returns_integer_with_alternative_key(self, graph, storage):
        """
        Tests that node.end_num returns integer using alternative key.

        Arrange: Storage with node and endlineno property
        Act: Get node and access end_num property
        Assert: Returns correct integer value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "endlineno", "50")
        node = graph.node("node1")
        assert node.end_num == 50

    def test_node_comment_returns_string(self, graph, storage):
        """
        Tests that node.comment returns string.

        Arrange: Storage with node and doccomment property
        Act: Get node and access comment property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "doccomment", "test comment")
        node = graph.node("node1")
        assert node.comment == "test comment"

    def test_node_type_returns_string(self, graph, storage):
        """
        Tests that node.type returns string.

        Arrange: Storage with node and type property
        Act: Get node and access type property
        Assert: Returns correct string value
        """
        storage.add_node("node1")
        storage.set_node_prop("node1", "type", "AST")
        node = graph.node("node1")
        assert node.type == "AST"
