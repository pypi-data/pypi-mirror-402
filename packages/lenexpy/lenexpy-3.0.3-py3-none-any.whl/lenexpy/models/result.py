
from typing import List, Optional

from lenexpy.models.course import Course
from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .split import Split
from .swimtime import SwimTime

from .relayposition import RelayPosition


class StatusResult(StrEnum):
    EXH = "EXH"
    DSQ = "DSQ"
    DNS = "DNS"
    DNF = "DNF"
    SICK = "SICK"
    WDR = "WDR"
    RJC = "RJC"


# TODO: confirm root tag for Result.
class Result(LenexBaseXmlModel, tag="RESULT"):
    comment: Optional[str] = attr(name="comment", default=None)
    eventid: int = attr(name="eventid")
    heatid: Optional[int] = attr(name="heatid", default=None)
    lane: Optional[int] = attr(name="lane", default=None)
    points: Optional[int] = attr(name="points", default=None)
    # Keep raw value so non-standard formats like "+80" are preserved.
    reactiontime: Optional[str] = attr(name="reactiontime", default=None)
    relay_positions: List[RelayPosition] = wrapped(
        "RELAYPOSITIONS",
        element(tag="RELAYPOSITION"),
        default_factory=list,
    )
    resultid: int = attr(name="resultid")
    # Allow arbitrary status strings (fixtures include RJC, etc.)
    status: Optional[StatusResult] = attr(name="status", default=None)
    splits: List[Split] = wrapped(
        "SPLITS",
        element(tag="SPLIT"),
        default_factory=list,
    )
    swimdistance: Optional[int] = attr(name="swimdistance", default=None)
    swimtime: SwimTime = attr(name="swimtime")
    entrytime: Optional[SwimTime] = attr(name="entrytime", default=None)
    late: Optional[str] = attr(name="late", default=None)
    entrycourse: Optional[Course] = attr(name="entrycourse", default=None)
