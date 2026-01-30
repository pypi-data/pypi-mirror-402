from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, wrapped, element

from lenexpy.models.base import LenexBaseXmlModel
from lenexpy.models.reactiontime import ReactionTime
from lenexpy.models.split import Split
from lenexpy.models.swimtime import SwimTime


class StatusResult(StrEnum):
    EXH = "EXH"
    DSQ = "DSQ"
    DNS = "DNS"
    DNF = "DNF"
    SICK = "SICK"
    WDR = "WDR"


# TODO: confirm root tag for Result.
class Result(LenexBaseXmlModel, tag="RESULT"):
    lane: int = attr(name="lane")
    swim_time: SwimTime = attr(name="swimtime")
    status: Optional[StatusResult] = attr(name="status", default=None)
    reaction_time: Optional[ReactionTime] = attr(name="reactiontime", default=None)
    splits: List[Split] = wrapped(
        "SPLITS",
        element(tag="SPLIT"),
        default_factory=list,
    )
