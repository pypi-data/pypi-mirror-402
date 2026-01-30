from lenexpy.strenum import StrEnum
from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel


class HandicapClass(StrEnum):
    C1 = "1"
    C2 = "2"
    C3 = "3"
    C4 = "4"
    C5 = "5"
    C6 = "6"
    C7 = "7"
    C8 = "8"
    C9 = "9"
    C10 = "10"
    C11 = "11"
    C12 = "12"
    C13 = "13"
    C14 = "14"
    C15 = "15"
    GER_AB = "GER.AB"
    GER_GB = "GER.GB"


# TODO: confirm root tag for Handicap.
class Handicap(LenexBaseXmlModel, tag="HANDICAP"):
    breast: HandicapClass = attr(name="breast")
    exception: Optional[str] = attr(name="exception", default=None)
    free: HandicapClass = attr(name="free")
    medley: HandicapClass = attr(name="medley")
