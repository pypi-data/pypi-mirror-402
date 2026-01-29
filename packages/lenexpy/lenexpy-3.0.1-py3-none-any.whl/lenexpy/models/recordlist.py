from datetime import datetime
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel
from .gender import Gender
from .agegroup import AgeGroup
from .course import Course
from .record import Record


# TODO: confirm root tag for RecordList.
class RecordList(LenexBaseXmlModel, tag="RECORDLIST"):
    agegroup: Optional[AgeGroup] = element(tag="AGEGROUP", default=None)
    course: Course = attr(name="course")
    gender: Gender = attr(name="gender")
    handicap: Optional[int] = attr(name="handicap", default=None)
    name: str = attr(name="name")
    nation: Optional[str] = attr(name="nation", default=None)
    order: Optional[int] = attr(name="order", default=None)
    records: List[Record] = wrapped(
        "RECORDS",
        element(tag="RECORD"),
        default_factory=list,
    )
    region: Optional[str] = attr(name="region", default=None)
    updated: Optional[datetime] = attr(name="updated", default=None)
    type: Optional[str] = attr(name="type", default=None)
