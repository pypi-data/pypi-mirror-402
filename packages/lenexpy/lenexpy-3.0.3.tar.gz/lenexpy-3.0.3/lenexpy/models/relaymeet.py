from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, wrapped, element

from .base import LenexBaseXmlModel

from .result import Result

from .entry import Entry
from .gender import Gender


# TODO: confirm root tag for RelayMeet.
class RelayMeet(LenexBaseXmlModel, tag="RELAY"):
    agemax: int = attr(name="agemax")
    agemin: int = attr(name="agemin")
    agetotalmax: int = attr(name="agetotalmax")
    agetotalmin: int = attr(name="agetotalmin")
    entries: List[Entry] = wrapped(
        "ENTRIES",
        element(tag="ENTRY"),
        default_factory=list,
    )
    gender: Gender = attr(name="gender")
    handicap: Optional[int] = attr(name="handicap", default=None)
    name: Optional[str] = attr(name="name", default=None)
    number: Optional[int] = attr(name="number", default=None)
    results: List[Result] = wrapped(
        "RESULTS",
        element(tag="RESULT"),
        default_factory=list,
    )
