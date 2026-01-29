from datetime import time
from typing import List, Optional, Union

from lenexpy.strenum import StrEnum
from pydantic import field_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .meetinfoentry import MeetInfoEntry
from .relayposition import RelayPosition
from .swimtime import SwimTime
from .course import Course


class Status(StrEnum):
    DNS = "DNS"
    DSQ = "DSQ"
    EXH = "EXH"
    RJC = "RJC"
    SICK = "SICK"
    WDR = "WDR"


# TODO: confirm root tag for Entry.
class Entry(LenexBaseXmlModel, tag="ENTRY"):
    agegroupid: Optional[int] = attr(name="agegroupid", default=None)
    entrycourse: Optional[Course] = attr(name="entrycourse", default=None)
    entrytime: Optional[SwimTime] = attr(name="entrytime", default=None)
    eventid: Optional[int] = attr(name="eventid", default=None)
    heatid: Optional[int] = attr(name="heatid", default=None)
    lane: Optional[int] = attr(name="lane", default=None)
    meetinfo: Optional[MeetInfoEntry] = element(tag="MEETINFO", default=None)
    relay_positions: List[RelayPosition] = element(
        tag="RELAYPOSITIONS",
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
