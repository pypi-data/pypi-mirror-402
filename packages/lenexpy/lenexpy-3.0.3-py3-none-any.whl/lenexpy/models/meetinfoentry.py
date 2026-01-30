from datetime import datetime, time as dtime
from typing import Optional

from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .pool import Pool
from .swimtime import SwimTime
from .course import Course


# TODO: confirm root tag for MeetInfoEntry.
class MeetInfoEntry(LenexBaseXmlModel, tag="MEETINFO"):
    approved: Optional[str] = attr(name="approved", default=None)
    city: Optional[str] = attr(name="city", default=None)
    course: Optional[Course] = attr(name="course", default=None)
    date: Optional[datetime] = attr(name="date", default=None)
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    name: Optional[str] = attr(name="name", default=None)
    nation: Optional[str] = attr(name="nation", default=None)
    pool: Optional[Pool] = element(tag="POOL", default=None)
    qualification_time: Optional[SwimTime] = attr(
        name="qualificationtime",
        default=None,
    )
    state: Optional[str] = attr(name="state", default=None)
