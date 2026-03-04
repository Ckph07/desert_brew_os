"""RabbitMQ consumer for production events.

Consumes messages from `production_events` queue and persists them into
finance_service database for auditability and asynchronous integrations.
"""
from __future__ import annotations

import json
import logging
import os
import time

import pika

from database import Base, SessionLocal, engine
import models  # noqa: F401
from models.production_event import ProductionEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = os.getenv("PRODUCTION_EVENTS_QUEUE", "production_events")
EXCHANGE = os.getenv("PRODUCTION_EXCHANGE", "production")


def _persist_event(routing_key: str, payload: dict) -> None:
    session = SessionLocal()
    try:
        event = ProductionEvent(
            routing_key=routing_key,
            event_name=payload.get("event_name", routing_key),
            payload=payload,
        )
        session.add(event)
        session.commit()
    finally:
        session.close()


def _on_message(channel, method, properties, body) -> None:
    try:
        payload = json.loads(body.decode("utf-8"))
        if not isinstance(payload, dict):
            payload = {"raw": payload}
        _persist_event(method.routing_key, payload)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logger.info("Consumed event: %s", method.routing_key)
    except Exception:  # pragma: no cover - defensive consumer loop
        logger.exception("Failed to process message")
        # avoid poison message infinite loop
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def consume_forever() -> None:
    Base.metadata.create_all(bind=engine)

    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.queue_bind(exchange=EXCHANGE, queue=QUEUE_NAME, routing_key="production.#")
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=_on_message)

            logger.info("Consumer connected. Waiting for events on queue '%s'", QUEUE_NAME)
            channel.start_consuming()
        except Exception:  # pragma: no cover - runtime retry loop
            logger.exception("Consumer disconnected. Retrying in 5 seconds")
            time.sleep(5)


if __name__ == "__main__":
    consume_forever()
