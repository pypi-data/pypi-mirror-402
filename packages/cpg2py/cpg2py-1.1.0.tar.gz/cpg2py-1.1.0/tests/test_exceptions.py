"""
Unit tests for custom exceptions.
"""
import pytest

from cpg2py._exceptions import (
    CPGError,
    EdgeNotFoundError,
    NodeNotFoundError,
    TopFileNotFoundError,
)


@pytest.mark.unit
class TestExceptions:
    """Test cases for custom exceptions."""

    def test_cpg_error_inherits_from_exception(self):
        """
        Tests that CPGError inherits from Exception.

        Arrange: None
        Act: Check inheritance
        Assert: CPGError is subclass of Exception
        """
        assert issubclass(CPGError, Exception)

    def test_node_not_found_error_inherits_from_cpg_error(self):
        """
        Tests that NodeNotFoundError inherits from CPGError.

        Arrange: None
        Act: Check inheritance
        Assert: NodeNotFoundError is subclass of CPGError
        """
        assert issubclass(NodeNotFoundError, CPGError)

    def test_node_not_found_error_default_message_contains_node_id(self):
        """
        Tests NodeNotFoundError with default message.

        Arrange: None
        Act: Create error with node ID
        Assert: Error message contains node ID and node_id attribute is set
        """
        error = NodeNotFoundError("node1")
        assert str(error) == "Node with id 'node1' not found in graph"
        assert error.node_id == "node1"

    def test_node_not_found_error_custom_message_uses_provided_message(self):
        """
        Tests NodeNotFoundError with custom message.

        Arrange: None
        Act: Create error with custom message
        Assert: Error message is custom message and node_id attribute is set
        """
        error = NodeNotFoundError("node1", "Custom error message")
        assert str(error) == "Custom error message"
        assert error.node_id == "node1"

    def test_edge_not_found_error_inherits_from_cpg_error(self):
        """
        Tests that EdgeNotFoundError inherits from CPGError.

        Arrange: None
        Act: Check inheritance
        Assert: EdgeNotFoundError is subclass of CPGError
        """
        assert issubclass(EdgeNotFoundError, CPGError)

    def test_edge_not_found_error_default_message_contains_edge_info(self):
        """
        Tests EdgeNotFoundError with default message.

        Arrange: None
        Act: Create error with edge info
        Assert: Error message contains edge info and attributes are set
        """
        error = EdgeNotFoundError("node1", "node2", "TYPE")
        assert str(error) == "Edge from 'node1' to 'node2' with type 'TYPE' not found in graph"
        assert error.from_id == "node1"
        assert error.to_id == "node2"
        assert error.edge_type == "TYPE"

    def test_edge_not_found_error_custom_message_uses_provided_message(self):
        """
        Tests EdgeNotFoundError with custom message.

        Arrange: None
        Act: Create error with custom message
        Assert: Error message is custom message and attributes are set
        """
        error = EdgeNotFoundError("node1", "node2", "TYPE", "Custom message")
        assert str(error) == "Custom message"
        assert error.from_id == "node1"
        assert error.to_id == "node2"
        assert error.edge_type == "TYPE"

    def test_top_file_not_found_error_inherits_from_cpg_error(self):
        """
        Tests that TopFileNotFoundError inherits from CPGError.

        Arrange: None
        Act: Check inheritance
        Assert: TopFileNotFoundError is subclass of CPGError
        """
        assert issubclass(TopFileNotFoundError, CPGError)

    def test_top_file_not_found_error_default_message_contains_node_id(self):
        """
        Tests TopFileNotFoundError with default message.

        Arrange: None
        Act: Create error with node ID
        Assert: Error message contains node ID and node_id attribute is set
        """
        error = TopFileNotFoundError("node1")
        assert str(error) == "Cannot find top file node from node 'node1'"
        assert error.node_id == "node1"

    def test_top_file_not_found_error_custom_message_uses_provided_message(self):
        """
        Tests TopFileNotFoundError with custom message.

        Arrange: None
        Act: Create error with custom message
        Assert: Error message is custom message and node_id attribute is set
        """
        error = TopFileNotFoundError("node1", "Custom message")
        assert str(error) == "Custom message"
        assert error.node_id == "node1"
