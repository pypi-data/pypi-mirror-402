from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .agegroup import AgeGroup
from .course import Course
from .gender import Gender
from .timestandard import TimeStandard


class TypeTimeStandardList(StrEnum):
    DEFAULT = "DEFAULT"
    MAXIMUM = "MAXIMUM"
    MINIMUM = "MINIMUM"


# TODO: confirm root tag for TimeStandardList.
class TimeStandardList(LenexBaseXmlModel, tag="TIMESTANDARDLIST"):
    id: int = attr(name="timestandardlistid")
    age_group: Optional[AgeGroup] = element(tag="AGEGROUP", default=None)
    course: Course = attr(name="course")
    gender: Gender = attr(name="gender")
    handicap: Optional[int] = attr(name="handicap", default=None)
    name: str = attr(name="name")
    code: Optional[str] = attr(name="code", default=None)
    # TODO: validate at least one time standard if required by contract.
    time_standards: List[TimeStandard] = wrapped(
        "TIMESTANDARDS",
        element(tag="TIMESTANDARD"),
        default_factory=list,
    )
    type: Optional[TypeTimeStandardList] = attr(name="type", default=None)
