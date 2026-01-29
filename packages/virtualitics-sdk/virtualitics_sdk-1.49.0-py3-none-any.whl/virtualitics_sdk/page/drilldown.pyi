from enum import Enum

class DrilldownType(Enum):
    FAST_MODAL: str
    MODAL: str
    POPOVER: str

class DrilldownSize(Enum):
    SMALL: str
    MEDIUM: str
    LARGE: str
    SHEET: str
