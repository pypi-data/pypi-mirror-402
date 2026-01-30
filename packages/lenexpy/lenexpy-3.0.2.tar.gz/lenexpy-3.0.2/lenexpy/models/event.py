from datetime import time as dtime
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic import model_validator
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .common import StatusEvent
from .fee import Fee
from .gender import Gender
from .heat import Heat
from .swimstyle import SwimStyle
from .timestandardref import TimeStandardRef
from .timing import Timing
from .agegroup import AgeGroup


class Round(StrEnum):
    TIM = "TIM"
    FHT = "FHT"
    FIN = "FIN"
    SEM = "SEM"
    QUA = "QUA"
    PRE = "PRE"
    SOP = "SOP"
    SOS = "SOS"
    SOQ = "SOQ"


class TypeEvent(StrEnum):
    EMPTY = "EMPTY"
    MASTERS = "MASTERS"


# TODO: confirm root tag for Event.
class Event(LenexBaseXmlModel, tag="EVENT"):
    agegroups: List[AgeGroup] = wrapped(
        "AGEGROUPS",
        element(tag="AGEGROUP"),
        default_factory=list,
    )
    daytime: Optional[dtime] = attr(name="daytime", default=None)
    eventid: int = attr(name="eventid")
    fee: Optional[Fee] = element(tag="FEE", default=None)
    gender: Optional[Gender] = attr(name="gender", default=None)
    heats: List[Heat] = wrapped(
        "HEATS",
        element(tag="HEAT"),
        default_factory=list,
    )
    maxentries: Optional[int] = attr(name="maxentries", default=None)
    number: int = attr(name="number")
    order: Optional[int] = attr(name="order", default=None)
    preveventid: Optional[int] = attr(name="preveventid", default=None)
    round: Optional[Round] = attr(name="round", default=None)
    run: Optional[int] = attr(name="run", default=None)
    status: Optional[StatusEvent] = attr(name="status", default=None)
    swimstyle: SwimStyle = element(tag="SWIMSTYLE")
    time_standard_refs: List[TimeStandardRef] = wrapped(
        "TIMESTANDARDREFS",
        element(tag="TIMESTANDARDREF"),
        default_factory=list,
    )
    timing: Optional[Timing] = attr(name="timing", default=None)
    type: Optional[TypeEvent] = attr(name="type", default=None)

    @model_validator(mode="after")
    def _validate_agegroups(self):
        if any(agegroup.id is None for agegroup in self.agegroups):
            raise ValueError("AGEGROUP elements inside EVENT must define agegroupid")
        return self
