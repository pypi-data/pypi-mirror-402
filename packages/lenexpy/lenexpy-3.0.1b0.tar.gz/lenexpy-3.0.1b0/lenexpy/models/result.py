from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .split import Split
from .swimtime import SwimTime

from .relayposition import RelayPosition
from .reactiontime import ReactionTime


class StatusResult(StrEnum):
    EXH = "EXH"
    DSQ = "DSQ"
    DNS = "DNS"
    DNF = "DNF"
    SICK = "SICK"
    WDR = "WDR"


# TODO: confirm root tag for Result.
class Result(LenexBaseXmlModel, tag="RESULT"):
    comment: Optional[str] = attr(name="comment", default=None)
    eventid: int = attr(name="eventid")
    heatid: Optional[int] = attr(name="heatid", default=None)
    lane: Optional[int] = attr(name="lane", default=None)
    points: Optional[int] = attr(name="points", default=None)
    reactiontime: Optional[ReactionTime] = attr(name="reactiontime", default=None)
    relay_positions: List[RelayPosition] = element(
        tag="RELAYPOSITIONS",
        default_factory=list,
    )
    resultid: int = attr(name="resultid")
    status: Optional[StatusResult] = attr(name="status", default=None)
    splits: List[Split] = element(tag="SPLITS", default_factory=list)
    swimtime: Optional[SwimTime] = attr(name="swimtime", default=None)
