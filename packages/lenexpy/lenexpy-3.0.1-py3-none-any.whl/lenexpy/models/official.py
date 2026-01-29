from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .nation import Nation
from .contact import Contact
from .gender import Gender


# TODO: confirm root tag for Official.
class Official(LenexBaseXmlModel, tag="OFFICIAL"):
    contact: Optional[Contact] = element(tag="CONTACT", default=None)
    firstname: str = attr(name="firstname")
    gender: Optional[Gender] = attr(name="gender", default=None)
    grade: Optional[str] = attr(name="grade", default=None)
    lastname: str = attr(name="lastname")
    license: Optional[str] = attr(name="license", default=None)
    nameprefix: Optional[str] = attr(name="nameprefix", default=None)
    nation: Optional[Nation] = attr(name="nation", default=None)
    officialid: int = attr(name="officialid")
    passport: Optional[str] = attr(name="passport", default=None)
