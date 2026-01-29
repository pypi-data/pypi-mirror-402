from typing import Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .reactiontime import ReactionTime
from .meetinfoentry import MeetInfoEntry


class StatusRelayPosition(StrEnum):
    DSQ = 'DSQ'
    DNF = 'DNF'


# TODO: confirm root tag for RelayPosition.
class RelayPosition(LenexBaseXmlModel, tag="RELAYPOSITION"):
    athleteid: Optional[int] = attr(name="athleteid", default=None)
    meetinfo: Optional[MeetInfoEntry] = element(tag="MEETINFO", default=None)
    number: int = attr(name="number")
    reaction_time: Optional[ReactionTime] = attr(name="reactiontime", default=None)
    status: Optional[StatusRelayPosition] = attr(name="status", default=None)
