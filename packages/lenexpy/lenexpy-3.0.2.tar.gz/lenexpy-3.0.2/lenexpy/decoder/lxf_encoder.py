from pathlib import Path
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from lenexpy.models.lenex import Lenex
from .lef_encoder import encode_lef_bytes


def encode_lxf(lenex: Lenex, filename: str):
    if not filename.endswith('.lxf'):
        raise TypeError('The file type must be .lxf')

    lxf_bytes = encode_lxf_bytes(lenex, Path(filename).name)
    with open(filename, "wb") as f:
        f.write(lxf_bytes)


def encode_lxf_bytes(lenex: Lenex, filename: str = "lenex.lxf") -> bytes:
    fn = Path(filename).name[:-4] + ".lef"
    xml_bytes = encode_lef_bytes(lenex)
    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zf:
        zf.writestr(fn, xml_bytes)
    return buffer.getvalue()
