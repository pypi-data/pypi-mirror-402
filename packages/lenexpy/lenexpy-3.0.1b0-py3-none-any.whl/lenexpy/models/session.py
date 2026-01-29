from datetime import datetime, time as dtime
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .event import Event
from .fee import Fee
from .judge import Judge
from .pool import Pool
from .course import Course


# TODO: confirm root tag for Session.
class Session(LenexBaseXmlModel, tag="SESSION"):
    course: Optional[Course] = attr(name="course", default=None)
    date: datetime = attr(name="date")
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    # TODO: validate at least one event if required by contract.
    events: List[Event] = wrapped(
        "EVENTS",
        element(tag="EVENT"),
        default_factory=list,
    )
    fees: List[Fee] = element(tag="FEES", default_factory=list)
    judges: List[Judge] = element(tag="JUDGES", default_factory=list)
    name: Optional[str] = attr(name="name", default=None)
    number: int = attr(name="number")
    officialmeeting: Optional[dtime] = attr(name="officialmeeting", default=None)
    pool: Optional[Pool] = element(tag="POOL", default=None)
    teamleadermeeting: Optional[dtime] = attr(
        name="teamleadermeeting",
        default=None,
    )
    warmupfrom: Optional[dtime] = attr(name="warmupfrom", default=None)
    warmupuntil: Optional[dtime] = attr(name="warmupuntil", default=None)
