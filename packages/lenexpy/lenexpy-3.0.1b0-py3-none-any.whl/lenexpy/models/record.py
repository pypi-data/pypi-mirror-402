from typing import List, Optional

from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .meetinforecord import MeetInfoRecord
from .relayrecord import RelayRecord
from .split import Split
from .swimstyle import SwimStyle
from .swimtime import SwimTime
from .athelete import Athlete


# TODO: confirm root tag for Record.
class Record(LenexBaseXmlModel, tag="RECORD"):
    athlete: Optional[Athlete] = element(tag="ATHLETE", default=None)
    comment: Optional[str] = attr(name="comment", default=None)
    meetinfo: Optional[MeetInfoRecord] = element(tag="MEETINFO", default=None)
    relay: Optional[RelayRecord] = element(tag="RELAY", default=None)
    splits: List[Split] = wrapped(
        "SPLITS",
        element(tag="SPLIT"),
        default_factory=list,
    )
    swimstyle: SwimStyle = element(tag="SWIMSTYLE")
    swimtime: SwimTime = attr(name="swimtime")
    status: Optional[str] = attr(name="status", default=None)
