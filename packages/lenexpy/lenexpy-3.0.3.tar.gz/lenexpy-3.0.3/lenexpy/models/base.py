from __future__ import annotations

from datetime import time as dtime
from typing import Any

from pydantic import ConfigDict, model_validator, model_serializer
from pydantic_xml import BaseXmlModel
from pydantic_xml.model import SearchMode


def _lenex_time_str(t: dtime) -> str:
    if t.microsecond == 0:
        if t.second == 0:
            return t.strftime("%H:%M")
        return t.strftime("%H:%M:%S")
    return t.isoformat()


def _convert_times(obj: Any) -> Any:
    if isinstance(obj, dtime):
        return _lenex_time_str(obj)
    if isinstance(obj, dict):
        return {k: _convert_times(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        t = [_convert_times(v) for v in obj]
        return t if isinstance(obj, list) else tuple(t)
    return obj


class LenexBaseXmlModel(BaseXmlModel):
    # ! DEV VERSION ! #
    # model_config = ConfigDict(
    #     arbitrary_types_allowed=True,
    #     extra="allow",
    #     protected_namespaces=(),
    #     search_mode="unordered",
    # )

    model_config = ConfigDict(
        arbitrary_types_allowed=False,
        extra="forbid",
    )
    __xml_search_mode__ = SearchMode.UNORDERED

    @model_validator(mode="before")
    @classmethod
    def _normalize_empty_strings(cls, data: Any):
        def normalize(value: Any):
            if isinstance(value, str) and value == "":
                return None
            if isinstance(value, list):
                return [normalize(item) for item in value]
            if isinstance(value, dict):
                return {key: normalize(val) for key, val in value.items()}
            return value

        if isinstance(data, (dict, list)):
            return normalize(data)
        return data

    @model_serializer(mode="wrap")
    def _lenex_serialize(self, handler, info):
        """
        Глобально приводит все datetime.time к нужному формату на выходе.
        Работает для всех наследников LenexBaseXmlModel.
        """
        data = handler(self)
        return _convert_times(data)
