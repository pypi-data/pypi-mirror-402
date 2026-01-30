from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel

from .swimtime import SwimTime


# TODO: confirm root tag for Split.
class Split(LenexBaseXmlModel, tag="SPLIT"):
    distance: Optional[int] = attr(name="distance", default=None)
    swimtime: Optional[SwimTime] = attr(name="swimtime", default=None)
