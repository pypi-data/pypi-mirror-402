from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element

from .base import LenexBaseXmlModel
from .gender import Gender

from .meetinfoentry import MeetInfoEntry
if TYPE_CHECKING:
    from .athelete import Athlete


class StatusRelayPosition(StrEnum):
    DSQ = 'DSQ'
    DNF = 'DNF'

# TODO: confirm root tag for RelayPosition.


class RelayPosition(LenexBaseXmlModel, tag="RELAYPOSITION"):
    # Relay positions in records embed a lightweight ATHLETE element.
    athlete: Optional[Athlete] = element(tag="ATHLETE", default=None)
    meetinfo: Optional[MeetInfoEntry] = element(tag="MEETINFO", default=None)
    athleteid: Optional[int] = attr(name="athleteid", default=None)
    number: Optional[int] = attr(name="number", default=None)
    # Preserve raw reaction time string (e.g., "+80") without validation.
    reaction_time: Optional[str] = attr(name="reactiontime", default=None)
    status: Optional[StatusRelayPosition] = attr(name="status", default=None)
