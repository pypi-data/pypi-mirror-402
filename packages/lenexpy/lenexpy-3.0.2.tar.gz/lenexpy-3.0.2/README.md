LenexPy
=======

Python toolkit for reading and writing Lenex 3.0 swimming data (.lef/.lxf). Models and validation follow the official Lenex technical documentation (Version 3.0, 4 Mar 2025) — see https://wiki.swimrankings.net/images/6/62/Lenex_3.0_Technical_Documentation.pdf.

What it does
------------
- Decode/encode Lenex XML (.lef) and zipped Lenex (.lxf).
- Pydantic + pydantic-xml data models aligned with the 4 Mar 2025 spec (required/optional attributes, timing modes, meet/session/event fields, etc.).
- JSON helpers to build Lenex objects and emit .lef/.lxf.

Install
-------
```bash
pip install lenexpy
```

Quick start
-----------
```python
from lenexpy import fromfile, tofile

lenex = fromfile("meet.lxf")      # .lxf / .lef / .xml
tofile(lenex, "out.lxf")
tofile(lenex, "out.lef")
```

Work with bytes directly:
```python
from lenexpy.decoder.lef_decoder import decode_lef_bytes
from lenexpy.decoder.lef_encoder import encode_lef_bytes
from lenexpy.decoder.lxf_decoder import decode_lxf_bytes
from lenexpy.decoder.lxf_encoder import encode_lxf_bytes

lenex = decode_lef_bytes(xml_bytes)
xml_bytes = encode_lef_bytes(lenex)

lenex = decode_lxf_bytes(lxf_bytes)
lxf_bytes = encode_lxf_bytes(lenex, "meet.lxf")
```

Build Lenex from JSON
---------------------
`scripts/parser.py` can create Lenex objects from JSON and write Lenex files.

```python
from scripts.parser import create_lenex_from_json_file
from lenexpy import tofile

lenex = create_lenex_from_json_file("meet.json")
tofile(lenex, "meet.lxf")
```

Minimal JSON shape:
```json
{
  "version": "3.0",
  "constructor": {
    "name": "Bot",
    "version": "1.0.0",
    "contact": {"email": "bot@example.com"}
  },
  "meet": {
    "name": "Test Meet",
    "city": "City",
    "nation": "RUS",
    "sessions": [
      {
        "number": 1,
        "date": "2025-01-01T00:00:00",
        "events": [
          {
            "eventid": 1,
            "number": 1,
            "swimstyle": {
              "distance": 50,
              "relaycount": 1,
              "stroke": "FREE"
            }
          }
        ]
      }
    ]
  }
}
```

Tests
-----
```bash
pytest
```
Fixture-based round trips live in `tests/fixtures`. Some third-party fixtures may xfail if they are not spec-conformant (e.g., missing required IDs).

Build
-----
```bash
python -m build
```
