import json
import logging

import pika

from .config import get_settings
from .database import SessionLocal, create_tables
from .integration import run_order_workflow
from .messaging import (
    EVENT_EXCHANGE,
    ORDER_PROCESSING_DLQ_ROUTING_KEY,
    ORDER_PROCESSING_QUEUE,
    ORDER_PROCESSING_RETRY_ROUTING_KEY,
    declare_topology,
    rabbitmq_connection,
)
from .models import Order, OrderStatus

LOGGER = logging.getLogger("swifttrack.worker")


def _retry_count(properties) -> int:
    headers = properties.headers or {}
    try:
        return int(headers.get("x-retry-count", 0))
    except (TypeError, ValueError):
        return 0


def _forward_properties(properties, headers: dict[str, object]) -> pika.BasicProperties:
    return pika.BasicProperties(
        content_type=properties.content_type or "application/json",
        delivery_mode=2,
        message_id=properties.message_id,
        type=properties.type or "order.created",
        headers=headers,
    )


def _publish_retry(channel, properties, body: bytes, retry_count: int) -> None:
    headers = dict(properties.headers or {})
    headers["x-retry-count"] = retry_count + 1
    channel.basic_publish(
        exchange=EVENT_EXCHANGE,
        routing_key=ORDER_PROCESSING_RETRY_ROUTING_KEY,
        body=body,
        properties=_forward_properties(properties, headers),
    )


def _publish_dead_letter(channel, properties, body: bytes, reason: str) -> None:
    headers = dict(properties.headers or {})
    headers["x-final-failure"] = reason[:500]
    channel.basic_publish(
        exchange=EVENT_EXCHANGE,
        routing_key=ORDER_PROCESSING_DLQ_ROUTING_KEY,
        body=body,
        properties=_forward_properties(properties, headers),
    )


def handle_message(channel, method, _properties, body: bytes) -> None:
    properties = _properties
    try:
        event = json.loads(body)
        if event.get("event_type") != "order.created":
            raise ValueError("Unsupported event type")

        order_id = event.get("order_id")
        if not order_id:
            raise ValueError("order.created event has no order_id")

        with SessionLocal() as db:
            order = db.get(Order, order_id)
            if order is None:
                raise ValueError(f"Order {order_id} does not exist")

            if order.status == OrderStatus.READY_FOR_DELIVERY:
                LOGGER.info("Skipping already completed order %s", order_id)
            else:
                LOGGER.info("Processing order %s from event %s", order_id, event.get("event_id"))
                run_order_workflow(db, order)

    except Exception as exc:
        retry_count = _retry_count(properties)
        try:
            if retry_count < get_settings().workflow_max_retries:
                _publish_retry(channel, properties, body, retry_count)
                LOGGER.warning(
                    "Order event failed; scheduled retry %s/%s: %s",
                    retry_count + 1,
                    get_settings().workflow_max_retries,
                    exc,
                )
            else:
                _publish_dead_letter(channel, properties, body, str(exc))
                LOGGER.error("Order event exhausted retries and was sent to the dead-letter queue")
            channel.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            LOGGER.exception("Could not route failed event; message will be requeued")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(delivery_tag=method.delivery_tag)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    create_tables()

    connection = rabbitmq_connection()
    try:
        channel = connection.channel()
        declare_topology(channel)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue=ORDER_PROCESSING_QUEUE,
            on_message_callback=handle_message,
            auto_ack=False,
        )
        LOGGER.info("SwiftTrack worker listening on %s", ORDER_PROCESSING_QUEUE)
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
