from lenexpy.strenum import StrEnum
from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel
from datetime import time as dtime


class Final(StrEnum):
    A = 'A'
    B = 'B'
    C = 'C'
    D = 'D'


class StatusHeat(StrEnum):
    SEEDED = 'SEEDED'
    INOFFICIAL = 'INOFFICIAL'
    OFFICIAL = 'OFFICIAL'


# TODO: confirm root tag for Heat.
class Heat(LenexBaseXmlModel, tag="HEAT"):
    agegroupid: Optional[int] = attr(name="agegroupid", default=None)
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    finaltype: Optional[Final] = attr(name="final", default=None)
    heatid: int = attr(name="heatid")
    number: int = attr(name="number")
    order: Optional[int] = attr(name="order", default=None)
    status: Optional[StatusHeat] = attr(name="status", default=None)
