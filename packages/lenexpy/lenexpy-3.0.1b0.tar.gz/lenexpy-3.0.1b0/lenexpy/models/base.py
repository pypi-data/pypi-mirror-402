from typing import Any

from pydantic import ConfigDict, model_validator
from pydantic_xml import BaseXmlModel


class LenexBaseXmlModel(BaseXmlModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
