from typing import Optional

from lenexpy.models.athelete import Athlete
from lenexpy.models.swimtime import SwimTime
from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element

from lenexpy.models.base import LenexBaseXmlModel


class Status(StrEnum):
    DNS = "DNS"
    DSQ = "DSQ"
    EXH = "EXH"
    RJC = "RJC"
    SICK = "SICK"
    WDR = "WDR"


# TODO: confirm root tag for Entry.
class Entry(LenexBaseXmlModel, tag="ENTRY"):
    entrytime: Optional[SwimTime] = attr(name="entrytime", default=None)
    lane: Optional[int] = attr(name="lane", default=None)
    status: Optional[Status] = attr(name="status", default=None)
    clubname: Optional[str] = attr(name="clubname", default=None)
    athlete: Optional[Athlete] = element(tag="ATHLETE", default=None)
