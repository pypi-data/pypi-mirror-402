from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr

from .base import LenexBaseXmlModel
from .stroke import Stroke


class Technique(StrEnum):
    DIVE = "DIVE"
    GLIDE = "GLIDE"
    KICK = "KICK"
    PULL = "PULL"
    START = "START"
    TURN = "TURN"


# TODO: confirm root tag for SwimStyle.
class SwimStyle(LenexBaseXmlModel, tag="SWIMSTYLE"):
    code: Optional[str] = attr(name="code", default=None)
    distance: int = attr(name="distance")
    name: Optional[str] = attr(name="name", default=None)
    relaycount: int = attr(name="relaycount")
    stroke: Stroke = attr(name="stroke")
    swimstyleid: Optional[int] = attr(name="swimstyleid", default=None)
    technique: Optional[Technique] = attr(name="technique", default=None)
