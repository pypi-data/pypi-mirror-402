from lenexpy.strenum import StrEnum
from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel
from .currency import Currency


class TypeFee(StrEnum):
    CLUB = "CLUB"
    ATHLETE = "ATHLETE"
    RELAY = "RELAY"
    TEAM = "TEAM"
    LATEENTRY_INDIVIDUAL = "LATEENTRY.INDIVIDUAL"
    LATEENTRY_RELAY = "LATEENTRY.RELAY"


# TODO: confirm root tag for Fee.
class Fee(LenexBaseXmlModel, tag="FEE"):
    currency: Optional[Currency] = attr(name="currency", default=None)
    type: Optional[TypeFee] = attr(name="type", default=None)
    value: Optional[int] = attr(name="value", default=None)
