import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from .topics import Topics

logger = logging.getLogger(__name__)


class KafkaProducer(ABC):
    def __init__(self, client):
        self.client = client
        self._producer = client.producer
        self._delivery_error: Optional[Exception] = None

    @property
    @abstractmethod
    def topic(self) -> Topics:
        pass

    def _delivery_callback(self, err, msg):
        """Callback invoked on message delivery success or failure."""
        if err is not None:
            self._delivery_error = err
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send(self, data):
        try:
            self._delivery_error = None
            serialized_data = json.dumps(data, default=self._json_serializer)

            self._producer.produce(
                topic=self.topic.value,
                value=serialized_data.encode("utf-8"),
                callback=self._delivery_callback,
            )

            # Block until the message is delivered (or timeout)
            remaining = self._producer.flush(timeout=10)

            if remaining > 0:
                raise Exception(f"Failed to deliver {remaining} message(s)")

            if self._delivery_error is not None:
                raise Exception(f"Delivery failed: {self._delivery_error}")

            logger.info(f"Data sent to Kafka topic {self.topic.value}")
        except Exception as e:
            logger.error(f"Error sending data to Kafka: {str(e)}")
            raise

    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json module"""
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
