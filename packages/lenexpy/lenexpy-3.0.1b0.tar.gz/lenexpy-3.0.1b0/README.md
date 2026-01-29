LenexPy
=======

Библиотека для чтения/записи LENEX (LEF/LXF) и преобразования "удобного JSON" в Lenex.

Основное
--------
- LEF: обычный XML Lenex.
- LXF: ZIP с одним LEF файлом внутри.
- Модели на pydantic-xml, сериализация/десериализация без изменения XML‑контракта.

Установка
---------
```bash
pip install lenexpy
```

Быстрый старт
-------------
Чтение/запись:
```python
from lenexpy import fromfile, tofile

lenex = fromfile("meet.lxf")   # .lxf / .lef / .xml
tofile(lenex, "out.lxf")
tofile(lenex, "out.lef")
```

Работа с bytes:
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

Удобный JSON -> Lenex
---------------------
Файл `parser.py` принимает простой JSON и строит Lenex.

```python
from parser import create_lenex_from_json_file
from lenexpy import tofile

lenex = create_lenex_from_json_file("meet.json")
tofile(lenex, "meet.lxf")
```

Минимальный JSON:
```json
{
  "version": "3.0",
  "constructor": {"name": "Bot", "version": "1.0.0"},
  "meet": {"name": "Test Meet", "city": "City", "nation": "RUS"}
}
```

Тесты
-----
```bash
pytest
```

Фикстуры кладите в `tests/fixtures` (поддержка вложенных папок).

Сборка
------
```bash
python -m build
```
