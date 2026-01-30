
from pathlib import Path

from lenexpy.decoder.lef_decoder import decode_lef
from lenexpy.decoder.lxf_decoder import decode_lxf
from lenexpy.models.lenex import Lenex


def decode(filename: str) -> Lenex:
    suffix = Path(filename).suffix.lower()
    if suffix in (".xml", ".lef"):
        return decode_lef(filename)
    if suffix == ".lxf":
        return decode_lxf(filename)
    raise TypeError("The file type must be .lxf, .lef, .xml")
