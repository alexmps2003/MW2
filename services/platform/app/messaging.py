import json
import uuid
from datetime import datetime, timezone

import pika

from .config import get_settings

EVENT_EXCHANGE = "swifttrack.events"
ORDER_CREATED_ROUTING_KEY = "order.created"
ORDER_PROCESSING_QUEUE = "swifttrack.order-processing"
ORDER_PROCESSING_RETRY_QUEUE = "swifttrack.order-processing.retry"
ORDER_PROCESSING_RETRY_ROUTING_KEY = "order.processing.retry"
ORDER_PROCESSING_DLQ = "swifttrack.order-processing.dlq"
ORDER_PROCESSING_DLQ_ROUTING_KEY = "order.processing.dead"


def rabbitmq_connection() -> pika.BlockingConnection:
    settings = get_settings()
    credentials = pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        virtual_host=settings.rabbitmq_vhost,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
        connection_attempts=3,
        retry_delay=2,
    )
    return pika.BlockingConnection(parameters)


def declare_topology(channel) -> None:
    settings = get_settings()
    channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="topic", durable=True)

    channel.queue_declare(
        queue=ORDER_PROCESSING_RETRY_QUEUE,
        durable=True,
        arguments={
            "x-message-ttl": max(1, settings.workflow_retry_delay_seconds * 1000),
            "x-dead-letter-exchange": EVENT_EXCHANGE,
            "x-dead-letter-routing-key": ORDER_CREATED_ROUTING_KEY,
        },
    )
    channel.queue_bind(
        queue=ORDER_PROCESSING_RETRY_QUEUE,
        exchange=EVENT_EXCHANGE,
        routing_key=ORDER_PROCESSING_RETRY_ROUTING_KEY,
    )

    channel.queue_declare(queue=ORDER_PROCESSING_DLQ, durable=True)
    channel.queue_bind(
        queue=ORDER_PROCESSING_DLQ,
        exchange=EVENT_EXCHANGE,
        routing_key=ORDER_PROCESSING_DLQ_ROUTING_KEY,
    )

    channel.queue_declare(
        queue=ORDER_PROCESSING_QUEUE,
        durable=True,
        arguments={
            "x-dead-letter-exchange": EVENT_EXCHANGE,
            "x-dead-letter-routing-key": ORDER_PROCESSING_DLQ_ROUTING_KEY,
        },
    )
    channel.queue_bind(
        queue=ORDER_PROCESSING_QUEUE,
        exchange=EVENT_EXCHANGE,
        routing_key=ORDER_CREATED_ROUTING_KEY,
    )


def publish_order_created(order_id: str) -> str:
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "order.created",
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "order_id": order_id,
    }
    connection = rabbitmq_connection()
    try:
        channel = connection.channel()
        declare_topology(channel)
        channel.basic_publish(
            exchange=EVENT_EXCHANGE,
            routing_key=ORDER_CREATED_ROUTING_KEY,
            body=json.dumps(event).encode("utf-8"),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=event["event_id"],
                type=event["event_type"],
            ),
        )
    finally:
        if connection.is_open:
            connection.close()
    return event["event_id"]
