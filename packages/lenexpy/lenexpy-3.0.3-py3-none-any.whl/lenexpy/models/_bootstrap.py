from __future__ import annotations
_BOOTSTRAPPED = False


def bootstrap_models() -> None:
    """
    Ensures pydantic-xml serializers are built after all model modules are loaded.
    Must be called before Lenex.from_xml / to_xml.
    """
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return

    # Импортируем корневую модель и "узлы" графа.
    # Важно: импорт внутри функции, чтобы не создавать круги при импорте пакета.
    from .lenex import Lenex

    # Эти импорты нужны, чтобы классы реально были в памяти и попали в namespace
    from .club import Club
    from .athelete import Athlete
    from .relayrecord import RelayRecord

    # Дополнительно (часто нужно) — базовые контейнеры цепочки:
    from .meet import Meet
    from .session import Session
    from .event import Event
    from .heat import Heat
    from .result import Result
    from .entry import Entry
    from .recordlist import RecordList
    from .record import Record
    from .relaymeet import RelayMeet
    from .relayposition import RelayPosition
    from .split import Split
    from .contact import Contact
    from .official import Official
    from .nation import Nation
    from .pool import Pool
    from .swimstyle import SwimStyle
    from .stroke import Stroke
    from .swimtime import SwimTime
    from .timestandardlist import TimeStandardList
    from .timestandard import TimeStandard
    from .timestandardref import TimeStandardRef
    from .timing import Timing
    from .agedate import AgeDate
    from .agegroup import AgeGroup
    from .fee import Fee
    from .qualify import Qualify
    from .ranking import Ranking
    from .pointtable import PointTable
    from .handicap import Handicap
    from .meetinfoentry import MeetInfoEntry
    from .meetinforecord import MeetInfoRecord

    ns = {
        "Lenex": Lenex,
        "Club": Club,
        "Athlete": Athlete,
        "RelayRecord": RelayRecord,
        "Meet": Meet,
        "Session": Session,
        "Event": Event,
        "Heat": Heat,
        "Result": Result,
        "Entry": Entry,
        "RecordList": RecordList,
        "Record": Record,
        "RelayMeet": RelayMeet,
        "RelayPosition": RelayPosition,
        "Split": Split,
        "Contact": Contact,
        "Official": Official,
        "Nation": Nation,
        "Pool": Pool,
        "SwimStyle": SwimStyle,
        "Stroke": Stroke,
        "SwimTime": SwimTime,
        "TimeStandardList": TimeStandardList,
        "TimeStandard": TimeStandard,
        "TimeStandardRef": TimeStandardRef,
        "Timing": Timing,
        "AgeDate": AgeDate,
        "AgeGroup": AgeGroup,
        "Fee": Fee,
        "Qualify": Qualify,
        "Ranking": Ranking,
        "PointTable": PointTable,
        "Handicap": Handicap,
        "MeetInfoEntry": MeetInfoEntry,
        "MeetInfoRecord": MeetInfoRecord,
    }

    # Главная часть: rebuild корневой модели (она должна получить __xml_serializer__)
    Lenex.model_rebuild(force=True, _types_namespace=ns)

    # На всякий случай "дожмём" ключевые узлы графа (это дешево, но стабилизирует)
    for m in (Club, Athlete, RelayRecord, RelayMeet, RelayPosition, Meet, Session, Event, Heat, Result, Entry, RecordList, Record):
        m.model_rebuild(force=True, _types_namespace=ns)

    _BOOTSTRAPPED = True


bootstrap_models()
