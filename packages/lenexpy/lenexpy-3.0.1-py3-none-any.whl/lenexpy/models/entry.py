from datetime import time
from typing import List, Optional, Union

from lenexpy.strenum import StrEnum
from pydantic import field_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .course import Course
from .handicap import HandicapClass
from .meetinfoentry import MeetInfoEntry
from .relayposition import RelayPosition
from .swimtime import SwimTime


class Status(StrEnum):
    EXH = "EXH"
    RJC = "RJC"
    SICK = "SICK"
    WDR = "WDR"


# TODO: confirm root tag for Entry.
class Entry(LenexBaseXmlModel, tag="ENTRY"):
    agegroupid: Optional[int] = attr(name="agegroupid", default=None)
    entrycourse: Optional[Course] = attr(name="entrycourse", default=None)
    entrydistance: Optional[int] = attr(name="entrydistance", default=None)
    entrytime: Optional[SwimTime] = attr(name="entrytime", default=None)
    eventid: int = attr(name="eventid")
    handicap: Optional[HandicapClass] = attr(name="handicap", default=None)
    heatid: Optional[int] = attr(name="heatid", default=None)
    lane: Optional[int] = attr(name="lane", default=None)
    meetinfo: Optional[MeetInfoEntry] = element(tag="MEETINFO", default=None)
    relay_positions: List[RelayPosition] = wrapped(
        "RELAYPOSITIONS",
        element(tag="RELAYPOSITION"),
        default_factory=list,
    )
    status: Optional[Status] = attr(name="status", default=None)

    @field_validator("entrytime", mode="before")
    @classmethod
    def _parse_entrytime(cls, value):
        if value is None or isinstance(value, SwimTime):
            return value
        if isinstance(value, (str, time)):
            return SwimTime._parse(value)
        return value
