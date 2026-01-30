from lenexpy.models.lenex import Lenex


def decode_lef(filename: str) -> Lenex:
    with open(filename, "rb") as file:
        return decode_lef_bytes(file.read())


def decode_lef_bytes(data: bytes) -> Lenex:
    return Lenex.from_xml(data)
