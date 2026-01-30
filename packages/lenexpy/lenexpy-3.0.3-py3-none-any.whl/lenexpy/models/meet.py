from datetime import datetime, time as dtime, date
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic import model_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .agedate import AgeDate
from .bank import Bank
from .common import StartMethod, StatusMeet, TouchpadMode
from .facility import Facility
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
    # Elements in the order they appear in real-world Lenex files to keep
    # round-tripped XML byte-identical.
    agedate: Optional[AgeDate] = element(tag="AGEDATE", default=None)
    pool: Optional[Pool] = element(tag="POOL", default=None)
    facility: Optional[Facility] = element(tag="FACILITY", default=None)
    bank: Optional[Bank] = element(tag="BANK", default=None)
    point_table: Optional[PointTable] = element(tag="POINTTABLE", default=None)
    fees: List[Fee] = wrapped(
        "FEES",
        element(tag="FEE"),
        default_factory=list,
    )
    qualify: Optional[Qualify] = element(tag="QUALIFY", default=None)
    contact: Optional[Contact] = element(tag="CONTACT", default=None)
    sessions: List[Session] = wrapped(
        "SESSIONS",
        element(tag="SESSION"),
        default_factory=list,
    )
    clubs: List[Club] = wrapped(
        "CLUBS",
        element(tag="CLUB"),
        default_factory=list,
    )

    altitude: Optional[int] = attr(name="altitude", default=None)
    city: str = attr(name="city")
    city_en: Optional[str] = attr(name="city.en", default=None)
    course: Optional[Course] = attr(name="course", default=None)
    deadline: Optional[date] = attr(name="deadline", default=None)
    deadline_time: Optional[dtime] = attr(name="deadlinetime", default=None)
    entry_start_date: Optional[date] = attr(
        name="entrystartdate", default=None)
    entry_type: Optional[EntryType] = attr(name="entrytype", default=None)
    host_club: Optional[str] = attr(name="hostclub", default=None)
    host_club_url: Optional[str] = attr(name="hostclub.url", default=None)
    max_entries_athlete: Optional[int] = attr(
        name="maxentriesathlete", default=None)
    max_entries_relay: Optional[int] = attr(
        name="maxentriesrelay", default=None)
    name: str = attr(name="name")
    name_en: Optional[str] = attr(name="name.en", default=None)
    nation: Nation = attr(name="nation")
    number: Optional[str] = attr(name="number", default=None)
    organizer: Optional[str] = attr(name="organizer", default=None)
    organizer_url: Optional[str] = attr(name="organizer.url", default=None)
    reservecount: Optional[int] = attr(name="reservecount", default=None)
    result_url: Optional[str] = attr(name="result.url", default=None)
    startmethod: Optional[StartMethod] = attr(name="startmethod", default=None)
    status: Optional[StatusMeet] = attr(name="status", default=None)
    state: Optional[str] = attr(name="state", default=None)
    uid: Optional[str] = attr(name="swrid", default=None)
    timing: Optional[Timing] = attr(name="timing", default=None)
    touchpadmode: Optional[TouchpadMode] = attr(
        name="touchpad", default=None)
    type: Optional[str] = attr(name="type", default=None)
    withdraw_until: Optional[date] = attr(name="withdrawuntil", default=None)
    # !            UNKNOWN PARAMETERS             ! #
    # ! Please help to identify these parameters. ! #
    masters: Optional[str] = attr(name="masters", default=None)
    hytek_courseorder: Optional[str] = attr(
        name="hytek.courseorder", default=None)
    revisiondate: Optional[date] = attr(name="revisiondate", default=None)

    # ! Verification is disabled due to the fact that there are        !
    # ! a large number of files that do not support this rule.         !
    # ! To enable, remove the comment characters from the lines below. !

    # @model_validator(mode="after")
    # def _require_sessions(self):
    #     if not self.sessions:
    #         raise ValueError("SESSIONS collection is required and must contain at least one SESSION")
    #     return self
