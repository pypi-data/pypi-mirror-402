from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr

from .base import LenexBaseXmlModel


class TypePool(StrEnum):
    INDOOR = "INDOOR"
    OUTDOOR = "OUTDOOR"
    LAKE = "LAKE"
    OCEAN = "OCEAN"


# TODO: confirm root tag for Pool.
class Pool(LenexBaseXmlModel, tag="POOL"):
    name: Optional[str] = attr(name="name", default=None)
    lanemax: Optional[int] = attr(name="lanemax", default=None)
    lanemin: Optional[int] = attr(name="lanemin", default=None)
    temperature: Optional[int] = attr(name="temperature", default=None)
    type: Optional[TypePool] = attr(name="type", default=None)
