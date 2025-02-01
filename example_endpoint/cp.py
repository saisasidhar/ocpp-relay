import asyncio
import logging
import sys
from datetime import datetime

import websockets
from ocpp.routing import on
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call, call_result
from ocpp.v201.enums import (
    ConnectorStatusType,
    MessageTriggerType,
    RegistrationStatusType,
)

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
    async def register_and_keep_alive(self):
        logger.info("Sending BootNotification")
        request = call.BootNotification(
            charging_station={"model": "ExampleModel", "vendor_name": "ExampleVendor"},
            reason="PowerUp",
        )
        response = await self.call(request)

        if response.status == RegistrationStatusType.accepted:
            logger.info("BootNotification accepted. Registered to central system")

            request = call.Heartbeat()
            while True:
                await asyncio.sleep(response.interval)
                logger.info("Sending HeartBeat")
                await self.call(request)

    async def _send_status_notification(self):
        await asyncio.sleep(0.5)
        logger.info("Sending StatusNotification to CSMS")
        request = call.StatusNotification(
            timestamp=datetime.utcnow().isoformat(),
            connector_status=ConnectorStatusType.available,
            evse_id=1,
            connector_id=1,
        )
        await self.call(request)

    @on("TriggerMessage")
    async def on_trigger_message(self, requested_message, **kwargs):
        if requested_message == MessageTriggerType.status_notification:
            logger.info(
                "Received trigger message from CSMS requesting for StatusNotification"
            )
            asyncio.create_task(self._send_status_notification())
        return call_result.TriggerMessage(status="Accepted")


async def main():
    async with websockets.connect(
        "ws://localhost:8500/CP00000007", subprotocols=["ocpp2.0.1"]
    ) as ws:
        cp = ChargePoint("CP00000007", ws)
        asyncio.create_task(cp.start())
        await cp.register_and_keep_alive()


if __name__ == "__main__":
    asyncio.run(main())
