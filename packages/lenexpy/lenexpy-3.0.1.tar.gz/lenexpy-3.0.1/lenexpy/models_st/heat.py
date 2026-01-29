from datetime import time as dtime
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, wrapped, element

from lenexpy.models.base import LenexBaseXmlModel
from .entry import Entry
from .result import Result


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
    heatid: int = attr(name="heatid")
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    name: Optional[str] = attr(name="name", default=None)
    number: Optional[int] = attr(name="number", default=None)
    order: Optional[int] = attr(name="order", default=None)
    status: Optional[StatusHeat] = attr(name="status", default=None)
    entries: List[Entry] = wrapped(
        "ENTRIES",
        element(tag="ENTRY"),
        default_factory=list,
    )
    reesults: List[Result] = wrapped(
        "RESULTS",
        element(tag="RESULT"),
        default_factory=list,
    )
