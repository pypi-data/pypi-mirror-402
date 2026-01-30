from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from lenexpy.strenum import StrEnum
from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .relayposition import RelayPosition

if TYPE_CHECKING:
    from .club import Club


class StatusRelayPosition(StrEnum):
    DSQ = 'DSQ'
    DNF = 'DNF'


# TODO: confirm root tag for RelayRecord.
class RelayRecord(LenexBaseXmlModel, tag="RELAY"):
    club: Optional[Club] = element(tag="CLUB", default=None)
    name: Optional[str] = attr(name="name", default=None)
    relay_positions: List[RelayPosition] = wrapped(
        "RELAYPOSITIONS",
        element(tag="RELAYPOSITION"),
        default_factory=list,
    )
