import asyncio
import json
import logging

import websockets

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_logger = logging.StreamHandler()
console_logger.setFormatter(
    logging.Formatter(
        "%(asctime)s - [%(levelname)-4.4s] - [%(threadName)-7.7s] - [%(name)-20.20s] - %(message)s"
    )
)
logger.addHandler(console_logger)

CSMS_URL = "ws://localhost:9000"


async def _relay(source_ws, target_ws, source_name, target_name):
    while True:
        try:
            message = await source_ws.recv()
            await target_ws.send(message)
            json_message = json.loads(message)
            logger.info(
                f"Relayed message from {source_name} to {target_name} ({json_message[1]})"
            )
        except websockets.exceptions.ConnectionClosed:
            logger.info(
                f"{source_name} connection closed."
            )  # Probably .recv() will be the one that raises an exception first??
            break


async def on_connect(cp_ws, path):
    charge_point_id = path.strip("/")
    try:
        ws_subprotocol = cp_ws.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logger.error(
            "Client didn't specify any sub-protocol. A sub-protocol is required for OCPP. Closing Connection"
        )
        return await cp_ws.close()

    logger.info(f"Received a new connection from a ChargePoint. {charge_point_id=}")
    logger.info(f"Connecting to CSMS at {CSMS_URL}/{charge_point_id}")
    async with websockets.connect(
        f"{CSMS_URL}/{charge_point_id}", subprotocols=[ws_subprotocol]
    ) as csms_ws:
        await asyncio.gather(
            _relay(cp_ws, csms_ws, source_name="CP", target_name="CSMS"),
            _relay(csms_ws, cp_ws, source_name="CSMS", target_name="CP"),
        )


async def main(port):
    server = await websockets.serve(on_connect, "0.0.0.0", port)
    logger.info(f"Relay server started on {port}")
    await server.wait_closed()


if __name__ == "__main__":
    # TODO Parameterize relay endpoint from command line argument
    asyncio.run(main(8500))
