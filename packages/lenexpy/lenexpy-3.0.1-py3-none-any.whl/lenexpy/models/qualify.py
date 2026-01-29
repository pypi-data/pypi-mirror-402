from datetime import date
from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr

from .base import LenexBaseXmlModel


class Conversion(StrEnum):
    NONE = "NONE"
    FINA_POINTS = "FINA_POINTS"
    PERCENT_LINEAR = "PERCENT_LINEAR"
    NON_CONFORMING_LAST = "NON_CONFORMING_LAST"


# TODO: confirm root tag for Qualify.
class Qualify(LenexBaseXmlModel, tag="QUALIFY"):
    conversion: Optional[Conversion] = attr(name="conversion", default=None)
    from_: date = attr(name="from")
    percent: Optional[int] = attr(name="percent", default=None)
    until: Optional[date] = attr(name="until", default=None)
