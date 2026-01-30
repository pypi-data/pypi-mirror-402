from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .swimstyle import SwimStyle
from .swimtime import SwimTime


# TODO: confirm root tag for TimeStandard.
class TimeStandard(LenexBaseXmlModel, tag="TIMESTANDARD"):
    swimstyle: SwimStyle = element(tag="SWIMSTYLE")
    swimtime: SwimTime = attr(name="swimtime")
