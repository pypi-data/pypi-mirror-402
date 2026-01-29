import abc
from typing import Any, Dict, Optional

from .._exceptions import NodeNotFoundError
from .storage import Storage


class AbcNodeQuerier(abc.ABC):
    """
    Abstract base class for node query operations.

    Provides interface for querying node properties and accessing node data.
    """

    def __init__(self, graph: Storage, nid: str) -> None:
        """
        Initializes a node querier.

        Args:
            graph: Storage instance containing the graph
            nid: Node ID to query

        Raises:
            NodeNotFoundError: If node does not exist in the graph
        """
        self.__nid: str = str(nid)
        self.__graph: Storage = graph
        if not graph.contains_node(self.__nid):
            raise NodeNotFoundError(nid)

    @property
    def node_id(self) -> str:
        """
        Returns the node ID.

        Returns:
            Node ID string
        """
        return self.__nid

    @property
    def properties(self) -> Optional[Dict[str, Any]]:
        """
        Returns all node properties.

        Returns:
            Dictionary of node properties, or None if node not found
        """
        return self.__graph.get_node_props(self.__nid)

    def get_property(self, *prop_names: str) -> Optional[Any]:
        """
        Gets a node property by trying multiple possible property names.

        Args:
            prop_names: Variable number of property name alternatives to try

        Returns:
            First found property value, or None if none found
        """
        prop_values = (self.__graph.get_node_prop(self.__nid, p_name) for p_name in prop_names)
        return next((value for value in prop_values if value is not None), None)
