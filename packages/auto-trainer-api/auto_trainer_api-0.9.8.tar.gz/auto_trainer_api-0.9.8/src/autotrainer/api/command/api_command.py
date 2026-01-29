from enum import IntEnum


class ApiCommand(IntEnum):
    """
    A command value is required for all command requests.
    """
    NONE = 0
    """No command.  Can be used to verify connection or that the receiver is configured to receive commands."""

    START_ACQUISITION = 100
    STOP_ACQUISITION = 110

    EMERGENCY_STOP = 200
    EMERGENCY_RESUME = 210

    GET_CONFIGURATION = 300
    """Response Payload: ConfigurationResponse"""

    GET_STATUS = 400
    """Response Payload: StatusResponse"""

    USER_DEFINED = 99999
    """A custom command defined between a particular commander and receiver.  Additional information can be 
    defined in the `data` field."""

    @classmethod
    def is_member(cls, value):
        return value in cls._value2member_map_

