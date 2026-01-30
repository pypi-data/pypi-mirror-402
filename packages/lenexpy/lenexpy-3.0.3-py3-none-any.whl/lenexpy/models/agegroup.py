from lenexpy.strenum import StrEnum
from typing import List, Optional, Union
from pydantic_xml import attr, wrapped, element

from .base import LenexBaseXmlModel

from .ranking import Ranking
from .gender import Gender


class Calculate(StrEnum):
    TOTAL: str = 'TOTAL'
    SINGLE: str = 'SINGLE'


# TODO: confirm root tag for AgeGroup.
class AgeGroup(LenexBaseXmlModel, tag="AGEGROUP"):
    id: Optional[int] = attr(name="agegroupid", default=None)
    agemax: int = attr(name="agemax")
    agemin: int = attr(name="agemin")
    gender: Optional[Gender] = attr(name="gender", default=None)
    calculate: Optional[Calculate] = attr(name="calculate", default=None)
    # list handicap, example "1,2,3", parsing for ,
    handicap: Optional[Union[int, str]] = attr(name="handicap", default=None)
    levelmax: Optional[int] = attr(name="levelmax", default=None)
    levelmin: Optional[int] = attr(name="levelmin", default=None)
    levels: Optional[str] = attr(name="levels", default=None)
    name: Optional[str] = attr(name="name", default=None)
    rankings: List[Ranking] = wrapped(
        "RANKINGS",
        element(tag="RANKING"),
        default_factory=list,
    )
