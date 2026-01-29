"""
API Service functionality for Autotrainer.
"""

from typing import Optional

from .api_event_kind import ApiEventKind
from .command import ApiCommand, ConfigurationResponse, StatusResponse
from .api_options import ApiOptions, create_default_api_options
from .rpc_service import ApiTopic, ApiCommandRequest, ApiCommandRequestResponse, ApiCommandReqeustResult, RpcService


def create_api_service(options: ApiOptions) -> Optional[RpcService]:
    from .zeromq import ZeroMQApiService

    # TODO Enable when ready
    # configure_telemetry(options.telemetry)

    if options.rpc.enable:
        return ZeroMQApiService(options.rpc)
    else:
        return None
