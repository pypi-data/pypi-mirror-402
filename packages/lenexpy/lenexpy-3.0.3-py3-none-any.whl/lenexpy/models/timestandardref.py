from typing import Optional

from pydantic_xml import attr, element

from .base import LenexBaseXmlModel

from .fee import Fee


# TODO: confirm root tag for TimeStandardRef.
class TimeStandardRef(LenexBaseXmlModel, tag="TIMESTANDARDREF"):
    time_standard_list_id: int = attr(name="timestandardlistid")
    fee: Optional[Fee] = element(tag="FEE", default=None)
    marker: Optional[str] = attr(name="marker", default=None)
