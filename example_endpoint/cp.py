import asyncio
import logging
import sys

import websockets
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call
from ocpp.v201.enums import RegistrationStatusType

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


async def main():
    async with websockets.connect(
        "ws://localhost:8500/CP00000007", subprotocols=["ocpp2.0.1"]
    ) as ws:
        cp = ChargePoint("CP00000007", ws)
        asyncio.create_task(cp.start())
        await cp.register_and_keep_alive()


if __name__ == "__main__":
    asyncio.run(main())
