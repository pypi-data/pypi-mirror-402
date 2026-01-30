from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel


class Bank(LenexBaseXmlModel, tag="BANK"):
    accountholder: str = attr(name="accountholder")
    bic: Optional[str] = attr(name="bic", default=None)
    iban: str = attr(name="iban")
    name: Optional[str] = attr(name="name", default=None)
    note: Optional[str] = attr(name="note", default=None)
