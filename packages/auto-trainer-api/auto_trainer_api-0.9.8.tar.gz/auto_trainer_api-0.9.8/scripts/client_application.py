"""
Create an instance of an Api Service implementation to received published messages and send command requests.
"""
import datetime
import logging
import time
from typing import Optional, Dict

from autotrainer.api import ApiCommandRequest, ApiCommandRequestResponse, ApiCommandReqeustResult, ApiCommand, \
    ConfigurationResponse, StatusResponse, ApiTopic, ApiEventKind
from autotrainer.api import create_api_service
from autotrainer.api import create_default_api_options
from autotrainer.api.command.status_response import ApiAppStatus, ApiTrainingMode


def _respond_to_command_request(request: ApiCommandRequest) -> ApiCommandRequestResponse:
    logger.debug("Received command request: %s", request.command)

    if request.command == ApiCommand.GET_CONFIGURATION:
        data = ConfigurationResponse("000000", "/home/ubuntu/Autotrainer", "/home/ubuntu/Documents/RawDataLocal",
                                     "/home/ubuntu/Autotrainer/animals", "/home/ubuntu/Documents/RawDataLocal/logs",
                                     "/home/ubuntu/Autotrainer/inference_model")
        return ApiCommandRequestResponse(result=ApiCommandReqeustResult.SUCCESS, data=data)
    elif request.command == ApiCommand.GET_STATUS:
        data = StatusResponse(app_status=ApiAppStatus.IDLE, training_mode=ApiTrainingMode.MANUAL, animal_id="123456")
        return ApiCommandRequestResponse(result=ApiCommandReqeustResult.SUCCESS, data=data, error_message="This is an error message")

    return ApiCommandRequestResponse(result=ApiCommandReqeustResult.SUCCESS, data={"seen": True})


def create_event_dict(kind: ApiEventKind, data: Optional[Dict]) -> dict:
    return {"kind": kind, "when": datetime.datetime.now(), "index": time.perf_counter_ns(), "context": data}


def run_server():
    options = create_default_api_options()

    service = create_api_service(options)

    service.command_request_delegate = _respond_to_command_request

    service.start()

    last_command = ""

    while True:
        line = ""
        while len(line) == 0:
            line = input(f"Enter event (?=help, enter='{last_command}'): ")
            if len(line) == 0 and len(last_command) != 0:
                break

        if len(line) == 0:
            line = last_command
        else:
            last_command = line

        argv = line.split()

        if len(argv) == 0:
            print("empty event, please type a event or ?")
            continue

        cmd = argv[0]
        params = argv[1:]

        try:
            if cmd == "?":
                print("No help available")

            elif cmd == "q" or cmd == "quit":
                break

            elif cmd == "app_launch":
                service.send_dict(ApiTopic.EVENT, create_event_dict(ApiEventKind.applicationLaunched, None))

            else:
                logger.warning("Unknown event: %s", cmd)

        except Exception as err:
            logger.exception("Error: %s", err)

    service.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s\t [%(name)s] %(message)s")
    logging.getLogger('autotrainer').setLevel(logging.DEBUG)
    logging.getLogger('tools').setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)

    run_server()
