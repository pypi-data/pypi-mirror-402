from typing import Optional

from pydantic_xml import attr, element

from .base import LenexBaseXmlModel
from .contact import Contact


# TODO: confirm root tag for Constructor.
class Constructor(LenexBaseXmlModel, tag="CONSTRUCTOR"):
    contact: Contact = element(tag="CONTACT")
    name: str = attr(name="name")
    registration: Optional[str] = attr(name="registration", default=None)
    version: str = attr(name="version")
