from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel
from .nation import Nation


class Facility(LenexBaseXmlModel, tag="FACILITY"):
    city: str = attr(name="city")
    nation: Nation = attr(name="nation")
    name: Optional[str] = attr(name="name", default=None)
    state: Optional[str] = attr(name="state", default=None)
    street: Optional[str] = attr(name="street", default=None)
    street2: Optional[str] = attr(name="street2", default=None)
    zip: Optional[str] = attr(name="zip", default=None)
