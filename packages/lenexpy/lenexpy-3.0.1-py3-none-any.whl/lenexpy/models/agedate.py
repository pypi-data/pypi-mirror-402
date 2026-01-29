from datetime import date

from lenexpy.strenum import StrEnum
from pydantic_xml import attr

from .base import LenexBaseXmlModel


class TypeAgeDate(StrEnum):
    YEAR = "YEAR"
    DATE = "DATE"
    POR = "POR"
    CAN_FNQ = "CAN.FNQ"
    LUX = "LUX"


# TODO: confirm root tag for AgeDate.
class AgeDate(LenexBaseXmlModel, tag="AGEDATE"):
    type: TypeAgeDate = attr(name="type")
    value: date = attr(name="value")
