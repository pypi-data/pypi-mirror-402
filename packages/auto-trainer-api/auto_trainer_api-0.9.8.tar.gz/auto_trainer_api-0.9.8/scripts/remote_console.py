import json
import logging

import zmq

from autotrainer.api.command.api_command import ApiCommand


def run_server():
    nonce = 1

    context = zmq.Context()
    req_socket = context.socket(zmq.REQ)
    req_socket.connect("tcp://127.0.0.1:5557")

    last_command = ""

    while True:
        line = ""
        while len(line) == 0:
            line = input(f"Enter command (?=help, enter='{last_command}'): ")
            if len(line) == 0 and len(last_command) != 0:
                break

        if len(line) == 0:
            line = last_command
        else:
            last_command = line

        argv = line.split()

        if len(argv) == 0:
            print("empty command, please type a command or ?")
            continue

        cmd = argv[0]
        params = argv[1:]

        try:
            if cmd == "?":
                print("No help available")

            elif cmd == "start":
                last_command = cmd

                req_socket.send_json({
                    "command": ApiCommand.START_ACQUISITION,
                    "nonce": nonce
                })

                message = req_socket.recv()
                print(f"Received reply: [ {message.decode('utf-8')} ]")

                nonce += 1

            elif cmd == "stop":
                last_command = cmd

                req_socket.send_json({
                    "command": ApiCommand.STOP_ACQUISITION,
                    "nonce": nonce
                })

                message = req_socket.recv()
                print(f"Received reply: [ {message.decode('utf-8')} ]")

                nonce += 1

            elif cmd == "configuration":
                last_command = cmd

                req_socket.send_json({
                    "command": ApiCommand.GET_CONFIGURATION,
                    "nonce": nonce
                })

                message = req_socket.recv()
                print(f"Received reply: {json.loads(message.decode('utf-8'))}")

                nonce += 1

            elif cmd == "status":
                last_command = cmd

                req_socket.send_json({
                    "command": ApiCommand.GET_STATUS,
                    "nonce": nonce
                })

                message = req_socket.recv()
                print(f"Received reply: {json.loads(message.decode('utf-8'))}")

                nonce += 1
            elif cmd == "q" or cmd == "quit":
                break
            else:
                logger.warning("Unknown command: %s", cmd)

        except Exception as err:
            logger.exception("Error: %s", err)

    logger.info("done")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s\t [%(name)s] %(message)s")
    logging.getLogger("autotrainer").setLevel(logging.DEBUG)
    logging.getLogger("tools").setLevel(logging.DEBUG)

    logger = logging.getLogger(__name__)

    run_server()
