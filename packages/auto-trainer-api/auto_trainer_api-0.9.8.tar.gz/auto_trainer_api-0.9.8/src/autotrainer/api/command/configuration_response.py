from dataclasses import dataclass


@dataclass
class ConfigurationResponse:
    device_id: str
    configuration_location: str
    data_location: str
    animal_location: str
    log_location: str
    inference_model: str
