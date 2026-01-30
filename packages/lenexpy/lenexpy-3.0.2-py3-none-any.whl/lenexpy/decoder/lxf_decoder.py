from io import BytesIO
from zipfile import ZipFile

from lenexpy.decoder.lef_decoder import decode_lef_bytes
from lenexpy.models.lenex import Lenex


def decode_lxf(filename: str) -> Lenex:
    with open(filename, "rb") as file:
        return decode_lxf_bytes(file.read())


def decode_lxf_bytes(data: bytes) -> Lenex:
    with ZipFile(BytesIO(data)) as zp:
        if not zp.filelist:
            raise TypeError("Incorrect lenex file")

        lef_members = [m for m in zp.filelist if m.filename.lower().endswith(".lef")]
        member = lef_members[0] if lef_members else zp.filelist[0]
        with zp.open(member) as file:
            return decode_lef_bytes(file.read())
