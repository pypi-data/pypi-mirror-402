from csv import DictReader
from pathlib import Path

from ._abc import *
from ._cpg import CpgGraph, CpgNode, CpgEdge
from ._exceptions import CPGError, EdgeNotFoundError, NodeNotFoundError, TopFileNotFoundError
from ._logger import get_logger

logger = get_logger(__name__)


def cpg_graph(node_csv: Path, edge_csv: Path, verbose: bool = False) -> CpgGraph:
    """
    Creates a CPG graph from CSV files.

    Args:
        node_csv: Path to the nodes CSV file
        edge_csv: Path to the edges CSV file
        verbose: If True, log warnings for duplicate nodes/edges

    Returns:
        Graph instance loaded from CSV files
    """
    storage = Storage()
    with open(node_csv, "r", encoding="utf-8") as n_file:
        reader = DictReader(n_file, delimiter="\t")
        for node_props in reader:
            nid = node_props.get("id:int", None)
            if nid is None:
                nid = node_props.get("id")
            if nid is None:
                continue
            if not storage.add_node(nid) and verbose:
                logger.warning("Node %s already exists in the graph", nid)
            if not storage.set_node_props(nid, node_props) and verbose:
                logger.warning("Failed to set properties for node %s", nid)
    with open(edge_csv, "r", encoding="utf-8") as f:
        reader = DictReader(f, delimiter="\t")
        for edge_props in reader:
            f_nid = str(edge_props.get("start", None))
            if f_nid is None:
                f_nid = str(edge_props.get("start:str"))
            t_nid = str(edge_props.get("end", None))
            if t_nid is None:
                t_nid = str(edge_props.get("end:str"))
            e_type = str(edge_props.get("type", None))
            if e_type is None:
                e_type = str(edge_props.get("type:str"))
            edge_id = (f_nid, t_nid, e_type)
            if not storage.contains_node(edge_id[0]):
                storage.add_node(edge_id[0])
                if verbose:
                    logger.warning("Node %s does not exist", edge_id[0])
            if not storage.contains_node(edge_id[1]):
                storage.add_node(edge_id[1])
                if verbose:
                    logger.warning("Node %s does not exist", edge_id[1])
            if not storage.add_edge(edge_id):
                if verbose:
                    logger.warning("Edge %s -> %s already exists in the graph", f_nid, t_nid)
            if not storage.set_edge_props(edge_id, edge_props):
                if verbose:
                    logger.warning("Failed to set properties for edge %s", edge_id)
    return CpgGraph(storage)


__all__ = [
    "cpg_graph",
    "CpgGraph",
    "CpgNode",
    "CpgEdge",
    "AbcGraphQuerier",
    "AbcNodeQuerier",
    "AbcEdgeQuerier",
    "Storage",
    "CPGError",
    "NodeNotFoundError",
    "EdgeNotFoundError",
    "TopFileNotFoundError",
]
