from dataclasses import dataclass
from enum import IntEnum


class ApiAppStatus(IntEnum):
    IDLE = 0
    ACQUIRING = 100
    CALIBRATION_DCS = 200
    CALIBRATION_3D = 300


class ApiTrainingMode(IntEnum):
    UNDEFINED = 0
    MANUAL = 100
    MANUAL_WITH_PROTOCOL = 200
    AUTOMATIC = 300

@dataclass
class StatusResponse:
    app_status: ApiAppStatus
    training_mode: ApiTrainingMode
    animal_id: str
