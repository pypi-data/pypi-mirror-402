import logging
from typing import List

from confluent_kafka import Producer, Consumer, KafkaException
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import NewTopic
from .topics import Topics

logger = logging.getLogger(__name__)


class KafkaClient:
    def __init__(self):
        self._admin = None
        self._producer = None
        self._consumer = None
        self._connected = False
        self._bootstrap_servers = []

    @property
    def bootstrap_servers(self):
        if not self._connected:
            raise ValueError("Cannot access bootstrap servers until connected")
        return self._bootstrap_servers

    @property
    def admin(self):
        if not self._connected:
            raise ValueError("Cannot access admin client until connected")
        return self._admin

    @property
    def producer(self):
        if self._producer is None:
            if not self._connected:
                raise ValueError("Cannot access producer until connected")
            self._producer = Producer(
                {"bootstrap.servers": ",".join(self._bootstrap_servers)}
            )
        return self._producer

    def create_consumer(self, group_id: str, **kwargs) -> Consumer:
        if not self._connected:
            raise ValueError("Cannot create consumer until connected")

        # Map kafka-python style kwargs to confluent-kafka config
        config = {
            "bootstrap.servers": ",".join(self._bootstrap_servers),
            "group.id": group_id,
        }

        # Map common config keys from snake_case to dot.notation
        key_mapping = {
            "auto_offset_reset": "auto.offset.reset",
            "enable_auto_commit": "enable.auto.commit",
            "session_timeout_ms": "session.timeout.ms",
            "max_poll_interval_ms": "max.poll.interval.ms",
        }

        for old_key, new_key in key_mapping.items():
            if old_key in kwargs:
                config[new_key] = kwargs.pop(old_key)

        # Remove kafka-python specific kwargs that don't apply
        kwargs.pop("value_deserializer", None)
        kwargs.pop("key_deserializer", None)

        # Add any remaining kwargs directly (already in confluent format)
        config.update(kwargs)

        self._consumer = Consumer(config)
        return self._consumer

    def connect(self, bootstrap_servers: List[str]):
        try:
            self._bootstrap_servers = bootstrap_servers
            self._admin = AdminClient(
                {
                    "bootstrap.servers": ",".join(bootstrap_servers),
                    "client.id": "taphealth-kafka-admin",
                }
            )
            self._connected = True

            topics = [topic.value for topic in Topics]
            self.create_topics(topics)

            logger.info(f"Connected to Kafka cluster at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"Error connecting to Kafka cluster: {e}")
            raise

    def create_topics(self, topics: List[str]):
        if not self._connected or self._admin is None:
            raise ValueError("Cannot create topics: not connected to Kafka")

        try:
            # Get existing topics from cluster metadata
            cluster_metadata = self._admin.list_topics(timeout=10)
            existing_topics = set(cluster_metadata.topics.keys())
            topics_to_create = [
                topic for topic in topics if topic not in existing_topics
            ]

            if not topics_to_create:
                logger.info("All topics already exist")
                return

            new_topics = [
                NewTopic(topic=topic, num_partitions=1, replication_factor=1)
                for topic in topics_to_create
            ]

            # create_topics returns a dict of futures
            futures = self._admin.create_topics(new_topics)

            # Wait for each topic creation to complete
            for topic, future in futures.items():
                try:
                    future.result()  # Block until topic is created
                    logger.info(f"Created topic: {topic}")
                except KafkaException as e:
                    if "TOPIC_ALREADY_EXISTS" in str(e):
                        logger.info(f"Topic {topic} already exists")
                    else:
                        raise

            logger.info(f"Created topics: {topics_to_create}")
        except KafkaException as e:
            if "TOPIC_ALREADY_EXISTS" in str(e):
                logger.info("Topics already exist")
            else:
                logger.error(f"Error creating topics: {e}")
                raise
        except Exception as e:
            logger.error(f"Error creating topics: {e}")
            raise

    def disconnect(self):
        if self._producer:
            self._producer.flush()  # Ensure all messages are delivered
            self._producer = None

        if self._consumer:
            self._consumer.close()
            self._consumer = None

        # AdminClient doesn't have a close method in confluent-kafka
        self._admin = None

        self._connected = False
        logger.info("Disconnected from Kafka")
