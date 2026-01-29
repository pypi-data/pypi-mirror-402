from __future__ import annotations

import abc
from typing import Any, Dict, Optional, Tuple

from .._exceptions import EdgeNotFoundError
from .storage import Storage


class AbcEdgeQuerier(abc.ABC):
    """
    Abstract base class for edge query operations.

    Provides interface for querying edge properties and accessing edge data.
    """

    def __init__(self, graph: Storage, f_nid: str, t_nid: str, e_type: int = 0) -> None:
        """
        Initializes an edge querier.

        Args:
            graph: Storage instance containing the graph
            f_nid: Source node ID
            t_nid: Target node ID
            e_type: Edge type/ID

        Raises:
            EdgeNotFoundError: If edge does not exist in the graph
        """
        self.__graph: Storage = graph
        self.__edge_id: Tuple[str, str, str] = (str(f_nid), str(t_nid), str(e_type))
        if not graph.contains_edge(self.__edge_id):
            raise EdgeNotFoundError(f_nid, t_nid, str(e_type))

    @property
    def edge_id(self) -> Tuple[str, str, int]:
        """
        Returns the edge ID tuple.

        Returns:
            Edge ID tuple (from_node, to_node, edge_type)
        """
        return self.__edge_id

    @property
    def from_nid(self) -> str:
        """
        Returns the source node ID.

        Returns:
            Source node ID string
        """
        return self.__edge_id[0]

    @property
    def to_nid(self) -> str:
        """
        Returns the target node ID.

        Returns:
            Target node ID string
        """
        return self.__edge_id[1]

    @property
    def edge_type(self) -> str:
        """
        Returns the edge type.

        Returns:
            Edge type string
        """
        return self.__edge_id[2]

    @property
    def properties(self) -> Optional[Dict[str, Any]]:
        """
        Returns all edge properties.

        Returns:
            Dictionary of edge properties, or None if edge not found
        """
        return self.__graph.get_edge_props(self.__edge_id)

    def get_property(self, *prop_names: str) -> Optional[Any]:
        """
        Gets an edge property by trying multiple possible property names.

        Args:
            prop_names: Variable number of property name alternatives to try

        Returns:
            First found property value, or None if none found
        """
        prop_values = (self.__graph.get_edge_prop(self.__edge_id, p_name) for p_name in prop_names)
        return next((value for value in prop_values if value is not None), None)
