from pathlib import Path

from lenexpy.models.lenex import Lenex
from .lef_encoder import encode_lef
from .lxf_encoder import encode_lxf


def encode(lenex: Lenex, filename: str):
    suffix = Path(filename).suffix.lower()
    if suffix in (".xml", ".lef"):
        return encode_lef(lenex, filename)
    if suffix == ".lxf":
        return encode_lxf(lenex, filename)
    raise TypeError("The file type must be .lxf, .lef, .xml")
