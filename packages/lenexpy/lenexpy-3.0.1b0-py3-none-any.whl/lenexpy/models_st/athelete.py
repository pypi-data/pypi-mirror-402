from datetime import date
from typing import Optional

from pydantic import model_validator
from pydantic_xml import attr, element

from lenexpy.models.base import LenexBaseXmlModel
from lenexpy.models.handicap import Handicap
from lenexpy.models.nation import Nation


# required_params = {'birthday', 'gender', 'firstname', 'lastname'}/


# TODO: confirm root tag for Athlete.
class Athlete(LenexBaseXmlModel, tag="ATHLETE"):
    athleteid: int = attr(name="athleteid")
    birthdate: date = attr(name="birthdate")
    firstname: str = attr(name="firstname")
    lastname: str = attr(name="lastname")
    handicap: Optional[Handicap] = element(tag="HANDICAP", default=None)
    nation: Optional[Nation] = attr(name="nation", default=None)

    @model_validator(mode="before")
    @classmethod
    def _map_id(cls, data):
        if isinstance(data, dict) and "id" in data and "athleteid" not in data:
            data["athleteid"] = data.pop("id")
        return data
