import asyncio
import logging
from datetime import datetime

import websockets
from ocpp.routing import on
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call, call_result
from ocpp.v201.enums import MessageTriggerType, RegistrationStatusType

logger = logging.getLogger()
logger.setLevel(logging.INFO)
console_logger = logging.StreamHandler()
console_logger.setFormatter(
    logging.Formatter(
        "%(asctime)s - [%(levelname)-4.4s] - [%(threadName)-7.7s] - [%(name)-20.20s] - %(message)s"
    )
)
logger.addHandler(console_logger)


class ChargePoint(cp):
    async def _send_trigger_message(self):
        await asyncio.sleep(0.5)
        logger.info(
            f"{self.id}: Sending TriggerMessage requesting for StatusNotification"
        )
        trigger_request = call.TriggerMessage(
            requested_message=MessageTriggerType.status_notification
        )
        await self.call(trigger_request)

    @on("Heartbeat")
    async def on_heartbeat(self, **kwargs):
        logger.info(f"{self.id}: Received Heartbeat.")
        asyncio.create_task(self._send_trigger_message())
        return call_result.Heartbeat(
            current_time=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )

    @on("BootNotification")
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        logger.info(f"{self.id}: Received BootNotification. Reason: {reason}")
        return call_result.BootNotification(
            current_time=datetime.utcnow().isoformat(),
            interval=60,
            status=RegistrationStatusType.accepted,
        )

    @on("StatusNotification")
    async def on_status_notification(self, **kwargs):
        logger.info(f"{self.id}: Received StatusNotification")
        return call_result.StatusNotification()

    @on("DataTransfer")
    async def on_data_transfer(self, **kwargs):
        logger.info(f"{self.id}: Received DataTransfer")
        return call_result.DataTransfer(status="Accepted")


async def on_connect(websocket, path):
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logger.error("Client hasn't requested any sub-protocol. Closing Connection")
        return await websocket.close()

    if websocket.subprotocol:
        logger.info(f"Expected sub-protocol: {websocket.subprotocol}")
    else:
        # In websockets lib if no sub-protocols are supported by the client and the server, it still proceeds without
        # a sub-protocol, so we have to manually close the connection.
        logger.warning(
            f"Protocols Mismatch | Expected sub-protocols: {websocket.available_subprotocols}, but client supports  {requested_protocols} | Closing connection"
        )
        return await websocket.close()

    charge_point_id = path.strip("/")
    cp = ChargePoint(charge_point_id, websocket)
    await cp.start()


async def main():
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9000, subprotocols=["ocpp2.0.1"]
    )
    logger.info("CSMS Started on port 9000")
    await server.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
