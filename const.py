from enum import Enum

SETTINGS_FILE = "config.json"

class TimelapseState(Enum):
    OFF = 1
    WAITING = 2
    RECORDING = 3