from datetime import datetime, date
from typing import List, Optional

from pydantic_xml import attr, element, wrapped

from .base import LenexBaseXmlModel

from .meet import Meet
from .recordlist import RecordList
from .timestandardlist import TimeStandardList
from .constructor import Constructor


# TODO: confirm root tag for Lenex.
class Lenex(LenexBaseXmlModel, tag="LENEX"):
    constructor: Constructor = element(tag="CONSTRUCTOR")
    meet: Optional[Meet] = wrapped(
        "MEETS",
        element(tag="MEET"),
        default=None,
    )
    record_lists: List[RecordList] = wrapped(
        "RECORDLISTS",
        element(tag="RECORDLIST"),
        default_factory=list,
    )
    time_standard_lists: List[TimeStandardList] = wrapped(
        "TIMESTANDARDLISTS",
        element(tag="TIMESTANDARDLIST"),
        default_factory=list,
    )
    created: Optional[datetime] = attr(name="created", default=None)
    revisiondate: Optional[date] = attr(name="revisiondate", default=None)
    version: str = attr(name="version")
