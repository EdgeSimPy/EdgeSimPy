from enum import StrEnum, auto


class PrivacyLevel(StrEnum):
    NONE = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    HIGHEST = auto()
