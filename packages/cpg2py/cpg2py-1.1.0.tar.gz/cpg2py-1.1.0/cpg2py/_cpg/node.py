from __future__ import annotations

from typing import List, Optional

from .._abc import AbcGraphQuerier, AbcNodeQuerier


class CpgNode(AbcNodeQuerier):
    def __init__(self, graph: AbcGraphQuerier, nid: str) -> None:
        super().__init__(graph, nid)

    @property
    def id(self) -> str:
        return self.node_id

    @property
    def code(self) -> Optional[str]:
        return self.get_property("code")

    @property
    def label(self) -> Optional[str]:
        return self.get_property("labels:label", "labels")

    @property
    def flags(self) -> List[str]:
        flags_str = self.get_property("flags:string_array", "flags:string[]", "flags")
        return str(flags_str).split(" ") if flags_str is not None else []

    @property
    def line_num(self) -> Optional[int]:
        linenum_str = str(self.get_property("lineno:int", "lineno"))
        return int(linenum_str) if linenum_str.isnumeric() else None

    @property
    def children_num(self) -> Optional[int]:
        num_str = str(self.get_property("childnum:int", "childnum"))
        return int(num_str) if num_str.isnumeric() else None

    @property
    def func_id(self) -> Optional[int]:
        fid_str = str(self.get_property("funcid:int", "funcid"))
        return int(fid_str) if fid_str.isnumeric() else None

    @property
    def class_name(self) -> Optional[str]:
        return self.get_property("classname")

    @property
    def namespace(self) -> Optional[str]:
        return self.get_property("namespace")

    @property
    def name(self) -> Optional[str]:
        return self.get_property("name")

    @property
    def end_num(self) -> Optional[int]:
        end_str = str(self.get_property("endlineno:int", "endlineno"))
        return int(end_str) if end_str.isnumeric() else None

    @property
    def comment(self) -> Optional[str]:
        return self.get_property("doccomment")

    @property
    def type(self) -> Optional[str]:
        return self.get_property("type")
