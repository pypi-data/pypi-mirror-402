from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel


# TODO: confirm root tag for Contact.
class Contact(LenexBaseXmlModel, tag="CONTACT"):
    city: Optional[str] = attr(name="city", default=None)
    country: Optional[str] = attr(name="country", default=None)
    email: str = attr(name="email")
    fax: Optional[str] = attr(name="fax", default=None)
    internet: Optional[str] = attr(name="internet", default=None)
    name: Optional[str] = attr(name="name", default=None)
    mobile: Optional[str] = attr(name="mobile", default=None)
    phone: Optional[str] = attr(name="phone", default=None)
    state: Optional[str] = attr(name="state", default=None)
    street: Optional[str] = attr(name="street", default=None)
    street2: Optional[str] = attr(name="street2", default=None)
    zip: Optional[str] = attr(name="zip", default=None)
