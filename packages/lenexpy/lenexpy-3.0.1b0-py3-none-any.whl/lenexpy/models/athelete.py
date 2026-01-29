from datetime import date
from typing import List, Optional

from pydantic import model_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel
from .entry import Entry
from .gender import Gender
from .handicap import Handicap
from .nation import Nation
from .result import Result


# required_params = {'birthday', 'gender', 'firstname', 'lastname'}/


# TODO: confirm root tag for Athlete.
class Athlete(LenexBaseXmlModel, tag="ATHLETE"):
    athleteid: int = attr(name="athleteid")
    birthdate: date = attr(name="birthdate")
    entries: List[Entry] = wrapped(
        "ENTRIES",
        element(tag="ENTRY"),
        default_factory=list,
    )
    firstname: str = attr(name="firstname")
    firstname_en: Optional[str] = attr(name="firstname.en", default=None)
    gender: Gender = attr(name="gender")
    handicap: Optional[Handicap] = element(tag="HANDICAP", default=None)
    lastname: str = attr(name="lastname")
    lastname_en: Optional[str] = attr(name="lastname.en", default=None)
    level: Optional[str] = attr(name="level", default=None)
    license: Optional[str] = attr(name="license", default=None)
    nameprefix: Optional[str] = attr(name="nameprefix", default=None)
    nation: Optional[Nation] = attr(name="nation", default=None)
    passport: Optional[str] = attr(name="passport", default=None)
    results: List[Result] = wrapped(
        "RESULTS",
        element(tag="RESULT"),
        default_factory=list,
    )
    swrid: Optional[int] = attr(name="swrid", default=None)

    @model_validator(mode="before")
    @classmethod
    def _map_id(cls, data):
        if isinstance(data, dict) and "id" in data and "athleteid" not in data:
            data["athleteid"] = data.pop("id")
        return data
