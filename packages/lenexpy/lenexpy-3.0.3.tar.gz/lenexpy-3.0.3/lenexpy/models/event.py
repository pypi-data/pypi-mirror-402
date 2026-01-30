from datetime import time as dtime
from typing import List, Optional

from lenexpy.strenum import StrEnum
from pydantic import field_serializer, field_validator, model_validator
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
    # Additional values observed in fixtures; keep here for reference while
    # allowing arbitrary strings through the model.
    EXTRAHEATS = "EXTRAHEATS"
    TIMETRIAL = "TIMETRIAL"


class TypeEvent(StrEnum):
    EMPTY = "EMPTY"
    MASTERS = "MASTERS"


# TODO: confirm root tag for Event.
class Event(LenexBaseXmlModel, tag="EVENT"):
    # Preserve child order observed in fixtures: SWIMSTYLE, AGEGROUPS,
    # TIMESTANDARDREFS, HEATS.
    swimstyle: SwimStyle = element(tag="SWIMSTYLE")
    agegroups: List[AgeGroup] = wrapped(
        "AGEGROUPS",
        element(tag="AGEGROUP"),
        default_factory=list,
    )
    time_standard_refs: List[TimeStandardRef] = wrapped(
        "TIMESTANDARDREFS",
        element(tag="TIMESTANDARDREF"),
        default_factory=list,
    )
    heats: List[Heat] = wrapped(
        "HEATS",
        element(tag="HEAT"),
        default_factory=list,
    )
    fee: Optional[Fee] = element(tag="FEE", default=None)

    daytime: Optional[dtime] = attr(name="daytime", default=None)
    eventid: int = attr(name="eventid")
    gender: Optional[Gender] = attr(name="gender", default=None)
    maxentries: Optional[int] = attr(name="maxentries", default=None)
    number: int = attr(name="number")
    order: Optional[int] = attr(name="order", default=None)
    preveventid: Optional[int] = attr(name="preveventid", default=None)
    # Use str to avoid dropping non-standard round values such as EXTRAHEATS
    # or TIMETRIAL found in fixtures.
    round: Optional[str] = attr(name="round", default=None)
    run: Optional[int] = attr(name="run", default=None)
    status: Optional[StatusEvent] = attr(name="status", default=None)
    timing: Optional[Timing] = attr(name="timing", default=None)
    type: Optional[TypeEvent] = attr(name="type", default=None)

    @model_validator(mode="after")
    def _validate_agegroups(self):
        if any(agegroup.id is None for agegroup in self.agegroups):
            raise ValueError(
                "AGEGROUP elements inside EVENT must define agegroupid")
        return self

    @field_validator("daytime", mode="before")
    @classmethod
    def _parse_daytime(cls, v):
        if v is None or v == "":
            return None
        if isinstance(v, dtime):
            return v
        # fromisoformat понимает "HH:MM", "HH:MM:SS", "HH:MM:SS.ffffff"
        return dtime.fromisoformat(v)

    @field_serializer("daytime")
    def _serialize_daytime(self, v: Optional[dtime], _info):
        if v is None:
            return None
        if v.second == 0 and v.microsecond == 0:
            return v.strftime("%H:%M")
        if v.microsecond == 0:
            return v.strftime("%H:%M:%S")

        # иначе ISO с микросекундами (стандартное поведение)
        return v.isoformat()
