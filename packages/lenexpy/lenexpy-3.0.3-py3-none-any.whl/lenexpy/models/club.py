from lenexpy.strenum import StrEnum
from typing import List, Optional
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .nation import Nation
from .official import Official
from .relaymeet import RelayMeet
from .contact import Contact
from .athelete import Athlete


class TypeClub(StrEnum):
    CLUB = "CLUB"
    NATIONALTEAM = "NATIONALTEAM"
    REGIONALTEAM = "REGIONALTEAM"
    UNATTACHED = "UNATTACHED"


# TODO: confirm root tag for Club.
class Club(LenexBaseXmlModel, tag="CLUB"):
    contact: Optional[Contact] = element(tag="CONTACT", default=None)
    code: Optional[str] = attr(name="code", default=None)
    clubid: Optional[int] = attr(name="clubid", default=None)
    athletes: List[Athlete] = wrapped(
        "ATHLETES",
        element(tag="ATHLETE"),
        default_factory=list,
    )
    name: Optional[str] = attr(name="name", default=None)
    name_en: Optional[str] = attr(name="name.en", default=None)
    nation: Optional[Nation] = attr(name="nation", default=None)
    number: Optional[int] = attr(name="number", default=None)
    officials: List[Official] = wrapped(
        "OFFICIALS",
        element(tag="OFFICIAL"),
        default_factory=list,
    )
    region: Optional[str] = attr(name="region", default=None)
    relays: List[RelayMeet] = wrapped(
        "RELAYS",
        element(tag="RELAY"),
        default_factory=list,
    )
    shortname: Optional[str] = attr(name="shortname", default=None)
    shortname_en: Optional[str] = attr(name="shortname.en", default=None)
    swrid: Optional[str] = attr(name="swrid", default=None)
    type: Optional[TypeClub] = attr(name="type", default=None)
