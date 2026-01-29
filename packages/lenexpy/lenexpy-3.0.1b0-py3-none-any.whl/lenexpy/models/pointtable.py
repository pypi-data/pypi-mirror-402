from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel


# TODO: confirm root tag for PointTable.
class PointTable(LenexBaseXmlModel, tag="POINTTABLE"):
    name: str = attr(name="name")
    point_table_id: Optional[int] = attr(name="pointtableid", default=None)
    version: str = attr(name="version")
