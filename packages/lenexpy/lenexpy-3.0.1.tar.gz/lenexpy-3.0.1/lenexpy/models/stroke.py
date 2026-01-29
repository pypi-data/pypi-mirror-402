from lenexpy.strenum import StrEnum


class Stroke(StrEnum):
    # Swimming stroke types
    FLY = "FLY"
    FREE = "FREE"
    BREAST = "BREAST"
    BACK = "BACK"

    # Underwater disciplines
    APNEA = "APNEA"
    IMMERSION = "IMMERSION"
    MEDLEY = "MEDLEY"
    SURFACE = "SURFACE"
    BIFINS = "BIFINS"

    # Unknown stroke type
    UNKNOWN = "UNKNOWN"
    CUSTOM = "CUSTOM"
