from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr

from .base import LenexBaseXmlModel


# TODO: confirm root tag for Ranking.
class Ranking(LenexBaseXmlModel, tag="RANKING"):
    order: Optional[int] = attr(name="order", default=None)
    place: int = attr(name="place")
    result_id: int = attr(name="resultid")
