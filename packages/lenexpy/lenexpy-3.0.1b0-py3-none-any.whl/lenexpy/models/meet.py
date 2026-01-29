from datetime import datetime, time as dtime, date
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .agedate import AgeDate
from .nation import Nation
from .pointtable import PointTable
from .pool import Pool
from .qualify import Qualify
from .session import Session
from .timing import Timing
from .course import Course
from .contact import Contact
from .club import Club
from .fee import Fee


class EntryType(StrEnum):
    OPEN = 'OPEN'
    INVITATION = 'INVITATION'


# TODO: confirm root tag for Meet.
class Meet(LenexBaseXmlModel, tag="MEET"):
    agedate: Optional[AgeDate] = element(tag="AGEDATE", default=None)
    altitude: Optional[int] = attr(name="altitude", default=None)
    city: str = attr(name="city")
    city_en: Optional[str] = attr(name="city.en", default=None)
    clubs: List[Club] = wrapped(
        "CLUBS",
        element(tag="CLUB"),
        default_factory=list,
    )
    contact: Optional[Contact] = element(tag="CONTACT", default=None)
    course: Optional[Course] = attr(name="course", default=None)
    deadline: Optional[date] = attr(name="deadline", default=None)
    deadline_time: Optional[dtime] = attr(name="deadlinetime", default=None)
    entry_start_date: Optional[date] = attr(name="entrystartdate", default=None)
    entry_type: Optional[EntryType] = attr(name="entrytype", default=None)
    fees: Optional[Fee] = element(tag="FEE", default=None)
    host_club: Optional[str] = attr(name="hostclub", default=None)
    host_club_url: Optional[str] = attr(name="hostclub.url", default=None)
    max_entries: Optional[int] = attr(name="maxentries", default=None)
    name: Optional[str] = attr(name="name", default=None)
    name_en: Optional[str] = attr(name="name.en", default=None)
    nation: Nation = attr(name="nation")
    number: Optional[str] = attr(name="number", default=None)
    organizer: Optional[str] = attr(name="organizer", default=None)
    organizer_url: Optional[str] = attr(name="organizer.url", default=None)
    point_table: Optional[PointTable] = element(tag="POINTTABLE", default=None)
    pool: Optional[Pool] = element(tag="POOL", default=None)
    qualify: Optional[Qualify] = element(tag="QUALIFY", default=None)
    result_url: Optional[str] = attr(name="result.url", default=None)
    sessions: List[Session] = wrapped(
        "SESSIONS",
        element(tag="SESSION"),
        default_factory=list,
    )
    state: Optional[str] = attr(name="state", default=None)
    uid: Optional[str] = attr(name="swrid", default=None)
    timing: Optional[Timing] = attr(name="timing", default=None)
    type: Optional[str] = attr(name="type", default=None)
