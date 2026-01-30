from lenexpy.strenum import StrEnum
from typing import List
from typing import Optional

from pydantic_xml import attr

from .base import LenexBaseXmlModel


class Role(StrEnum):
    OTH = "OTH"
    MDR = "MDR"
    TDG = "TDG"
    REF = "REF"
    STA = "STA"
    ANN = "ANN"
    JOS = "JOS"
    CTIK = "CTIK"
    TIK = "TIK"
    CFIN = "CFIN"
    FIN = "FIN"
    CIOT = "CIOT"
    IOT = "IOT"
    FSR = "FSR"
    COC = "COC"
    CREC = "CREC"
    REC = "REC"
    CRS = "CRS"
    CR = "CR"
    MED = "MED"


# TODO: confirm root tag for Judge.
class Judge(LenexBaseXmlModel, tag="JUDGE"):
    number: Optional[int] = attr(name="number", default=None)
    officialid: int = attr(name="officialid")
    remarks: Optional[str] = attr(name="remarks", default=None)
    role: Optional[Role] = attr(name="role", default=None)
    status: Optional[str] = attr(name="status", default=None)
