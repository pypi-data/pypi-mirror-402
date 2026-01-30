from lenexpy.strenum import StrEnum


class StartMethod(StrEnum):
    ONE_START = "1"
    TWO_STARTS = "2"


class TouchpadMode(StrEnum):
    ONESIDE = "ONESIDE"
    BOTHSIDE = "BOTHSIDE"


class StatusMeet(StrEnum):
    ENTRIES = "ENTRIES"
    SEEDED = "SEEDED"
    RUNNING = "RUNNING"
    OFFICIAL = "OFFICIAL"


class StatusSession(StrEnum):
    ENTRIES = "ENTRIES"
    SEEDED = "SEEDED"
    RUNNING = "RUNNING"
    UNOFFICIAL = "UNOFFICIAL"
    OFFICIAL = "OFFICIAL"


class StatusEvent(StrEnum):
    ENTRIES = "ENTRIES"
    SEEDED = "SEEDED"
    RUNNING = "RUNNING"
    UNOFFICIAL = "UNOFFICIAL"
    OFFICIAL = "OFFICIAL"
