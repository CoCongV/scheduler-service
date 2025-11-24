import os
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import AsyncIO
from scheduler_service.config import Config


if os.getenv("UNIT_TESTS") == "1":
    broker = StubBroker()
    broker.emit_after("process_boot")
else:
    broker = RabbitmqBroker(url=Config.DRAMATIQ_URL)

broker.add_middleware(AsyncIO())
dramatiq.set_broker(broker)
