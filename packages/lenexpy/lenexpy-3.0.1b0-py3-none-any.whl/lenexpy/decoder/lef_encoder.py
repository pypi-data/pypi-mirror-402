from lenexpy.models.lenex import Lenex

ENCODING = 'utf-8'


def encode_lef_bytes(lenex: Lenex) -> bytes:
    xml_value = lenex.to_xml(encoding=ENCODING, xml_declaration=True)
    if isinstance(xml_value, str):
        return xml_value.encode(ENCODING)
    return xml_value


def encode_lef(lenex: Lenex, filename: str):
    if not filename.endswith(('.lef', '.xml')):
        raise TypeError('The file type must be .lef, .xml')

    xml_string = encode_lef_bytes(lenex)
    with open(filename, "wb") as f:
        f.write(xml_string)
