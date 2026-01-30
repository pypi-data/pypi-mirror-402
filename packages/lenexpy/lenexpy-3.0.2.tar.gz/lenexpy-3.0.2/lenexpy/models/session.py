from datetime import datetime, time as dtime
from typing import List, Optional

from pydantic import model_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .common import StatusSession, TouchpadMode
from .course import Course
from .event import Event
from .fee import Fee
from .judge import Judge
from .pool import Pool
from .timing import Timing


# TODO: confirm root tag for Session.
class Session(LenexBaseXmlModel, tag="SESSION"):
    course: Optional[Course] = attr(name="course", default=None)
    date: datetime = attr(name="date")
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    endtime: Optional[dtime] = attr(name="endtime", default=None)
    events: List[Event] = wrapped(
        "EVENTS",
        element(tag="EVENT"),
        default_factory=list,
    )
    fees: List[Fee] = wrapped(
        "FEES",
        element(tag="FEE"),
        default_factory=list,
    )
    judges: List[Judge] = wrapped(
        "JUDGES",
        element(tag="JUDGE"),
        default_factory=list,
    )
    maxentriesathlete: Optional[int] = attr(name="maxentriesathlete", default=None)
    maxentriesrelay: Optional[int] = attr(name="maxentriesrelay", default=None)
    name: Optional[str] = attr(name="name", default=None)
    number: int = attr(name="number")
    officialmeeting: Optional[dtime] = attr(name="officialmeeting", default=None)
    pool: Optional[Pool] = element(tag="POOL", default=None)
    remarksjudge: Optional[str] = attr(name="remarksjudge", default=None)
    status: Optional[StatusSession] = attr(name="status", default=None)
    teamleadermeeting: Optional[dtime] = attr(
        name="teamleadermeeting",
        default=None,
    )
    timing: Optional[Timing] = attr(name="timing", default=None)
    touchpadmode: Optional[TouchpadMode] = attr(name="touchpadmode", default=None)
    warmupfrom: Optional[dtime] = attr(name="warmupfrom", default=None)
    warmupuntil: Optional[dtime] = attr(name="warmupuntil", default=None)

    @model_validator(mode="after")
    def _require_events(self):
        if not self.events:
            raise ValueError("EVENTS collection is required and must contain at least one EVENT")
        return self
