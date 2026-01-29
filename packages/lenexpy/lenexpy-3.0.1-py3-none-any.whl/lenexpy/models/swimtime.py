from datetime import time
from typing import TYPE_CHECKING, Union

from pydantic_core import core_schema

from lenexpy.strenum import StrEnum


class SwimTimeAttr(StrEnum):
    # NT - Not Time or
    NT = 'NT'


class SwimTime:
    if TYPE_CHECKING:
        NT: 'SwimTime'

    def __init__(self, hour: int, minute: int, second: int, hsec: int):
        self.attrib = None
        self.hour = hour
        self.minute = minute
        self.second = second
        self.hsec = hsec

    @classmethod
    def from_attrib(cls, attrib: SwimTimeAttr) -> 'SwimTime':
        self = cls(0, 0, 0, 0)
        self.attrib = attrib
        return self

    @classmethod
    def _parse(cls, t: Union[time, str]):
        if isinstance(t, str):
            t = t.strip()
            if t == SwimTimeAttr.NT:
                return cls.from_attrib(t)
            t = time.fromisoformat(t)
        return cls(t.hour, t.minute, t.second, t.microsecond // 10000)

    def __str__(self):
        if self.attrib is not None:
            return self.attrib
        return "%02d:%02d:%02d.%02d" % (self.hour, self.minute, self.second, self.hsec)

    def as_duration(self):
        return self.hour*60*60 + self.minute*60 + self.second + self.hsec / 100

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        def validate(value, _info):
            if isinstance(value, cls):
                return value
            if isinstance(value, (str, time)):
                return cls._parse(value)
            return value

        return core_schema.with_info_before_validator_function(
            validate,
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.str_schema(),
                    core_schema.time_schema(),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v),
                return_schema=core_schema.str_schema(),
            ),
        )


SwimTime.NT = SwimTime.from_attrib(SwimTimeAttr.NT)
