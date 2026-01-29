import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from .topics import Topics
from .client import KafkaClient  # Added import

logger = logging.getLogger(__name__)


class KafkaConsumer(ABC):
    def __init__(self, client: KafkaClient):  # Type hint for client
        self.client = client

    @property
    @abstractmethod
    def topic(self) -> Topics:
        pass

    @property
    @abstractmethod
    def group_id(self) -> str:
        pass

    @abstractmethod
    def on_message(self, data: Any, message: Any) -> None:
        pass

    def ensure_topics_exist(self):
        """Ensures that the topic this consumer subscribes to exists."""
        self.client.create_topics([self.topic.value])
        logger.info(f"Ensured topic {self.topic.value} exists.")

    def consume(self):
        self.ensure_topics_exist()  # Call to ensure topic exists
        consumer = self.client.create_consumer(
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )

        consumer.subscribe([self.topic.value])
        logger.info(f"Started consuming from topic {self.topic.value}")

        try:
            while True:
                # Poll for messages with 1 second timeout
                message = consumer.poll(timeout=1.0)

                if message is None:
                    # No message received within timeout
                    continue

                if message.error():
                    logger.error(f"Consumer error: {message.error()}")
                    continue

                # Deserialize the message value
                try:
                    raw_value = message.value()
                    if raw_value is not None:
                        data = json.loads(raw_value.decode("utf-8"))
                    else:
                        data = None
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    continue

                logger.info(
                    f"Received message on topic {self.topic.value} "
                    f"and partition {message.partition()}"
                )
                self.on_message(data, message)

        except KeyboardInterrupt:
            logger.info("Stopping consumer due to keyboard interrupt")
        except Exception as e:
            logger.error(f"Error consuming message: {str(e)}")
        finally:
            consumer.close()
            logger.info("Consumer closed")
