"""Optional Kafka producer (kafka-python), created lazily once per process.

    from util.kafka import publish
    publish(settings, settings.KAFKA_TOPIC_FILE_EXTRACTION, {"uploadId": upload_id})

``publish`` raises ``ConfigurationError`` when ``BE_KAFKA_BOOTSTRAP_SERVERS`` is
unset; callers that treat Kafka as best-effort should check
``settings.kafka_configured`` first. The producer is flushed/closed by the app
lifespan (``close_kafka_producer``).
"""

from __future__ import annotations

import json
import threading
from typing import TYPE_CHECKING, Any

from loguru import logger

from core.errors import ConfigurationError

if TYPE_CHECKING:
    from core.config import Settings

_lock = threading.Lock()
_producer: Any | None = None


def _serialize(value: Any) -> bytes:
    return json.dumps(value, default=str, separators=(",", ":")).encode("utf-8")


def get_kafka_producer(settings: Settings) -> Any:
    global _producer
    if not settings.kafka_configured:
        raise ConfigurationError("Kafka is not configured")
    if _producer is None:
        with _lock:
            if _producer is None:
                from kafka import KafkaProducer

                servers = settings.KAFKA_BOOTSTRAP_SERVERS or ""
                _producer = KafkaProducer(
                    bootstrap_servers=[s.strip() for s in servers.split(",") if s.strip()],
                    client_id=settings.KAFKA_CLIENT_ID or settings.APP_NAME,
                    value_serializer=_serialize,
                    key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
                    acks="all",
                    linger_ms=5,
                )
    return _producer


def publish(settings: Settings, topic: str | None, value: Any, *, key: str | None = None) -> None:
    """Fire-and-forget send (the client batches; delivery errors are logged)."""
    if not topic:
        raise ConfigurationError("Kafka topic is not configured")
    future = get_kafka_producer(settings).send(topic, value=value, key=key)
    future.add_errback(lambda exc: logger.error("Kafka delivery to {} failed: {}", topic, exc))


def close_kafka_producer(timeout: float = 5.0) -> None:
    global _producer
    with _lock:
        producer, _producer = _producer, None
    if producer is not None:
        try:
            producer.flush(timeout=timeout)
            producer.close(timeout=timeout)
        except Exception as exc:  # noqa: BLE001  # shutdown must not raise
            logger.warning("Kafka producer close failed: {}", exc)
