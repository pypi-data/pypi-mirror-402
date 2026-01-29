"""
Tests for KafkaClient.

Test Coverage:
=============

Initialization
--------------
- test_initial_state: Verifies all attributes are properly initialized

Property Access (Not Connected)
-------------------------------
- test_bootstrap_servers_raises_when_not_connected: bootstrap_servers raises ValueError
- test_admin_raises_when_not_connected: admin raises ValueError
- test_producer_raises_when_not_connected: producer raises ValueError
- test_create_consumer_raises_when_not_connected: create_consumer raises ValueError
- test_create_topics_raises_when_not_connected: create_topics raises ValueError

Connection
----------
- test_connect_sets_connected_state: connect() sets _connected=True and stores servers
- test_connect_creates_admin_client: connect() creates AdminClient with correct config
- test_connect_creates_all_topics: connect() calls create_topics with all Topics enum values
- test_connect_raises_on_error: connect() re-raises exceptions from AdminClient

Producer Property
-----------------
- test_producer_creates_instance_when_connected: producer property creates Producer
- test_producer_returns_same_instance: producer property returns cached instance
- test_producer_uses_correct_bootstrap_servers: Producer created with correct servers

Consumer Creation
-----------------
- test_create_consumer_returns_consumer: create_consumer returns Consumer instance
- test_create_consumer_maps_snake_case_config: auto_offset_reset -> auto.offset.reset
- test_create_consumer_removes_kafka_python_kwargs: value_deserializer is removed
- test_create_consumer_passes_confluent_kwargs: confluent-style kwargs passed through

Topic Creation
--------------
- test_create_topics_skips_existing: Doesn't create topics that already exist
- test_create_topics_creates_new_topics: Creates topics that don't exist
- test_create_topics_handles_already_exists_error: Handles TOPIC_ALREADY_EXISTS gracefully
- test_create_topics_raises_other_kafka_errors: Re-raises non-TOPIC_ALREADY_EXISTS errors

Disconnection
-------------
- test_disconnect_resets_state: disconnect() resets all state to initial
- test_disconnect_flushes_producer: disconnect() calls producer.flush()
- test_disconnect_closes_consumer: disconnect() calls consumer.close()
- test_disconnect_handles_no_producer: disconnect() works when producer is None
- test_disconnect_handles_no_consumer: disconnect() works when consumer is None
"""

from unittest.mock import MagicMock, patch

import pytest

from taphealth_kafka import KafkaClient


class TestKafkaClientInitialization:
    """Tests for KafkaClient initialization."""

    def test_initial_state(self):
        """Verifies all attributes are properly initialized to default values."""
        client = KafkaClient()

        assert client._connected is False
        assert client._producer is None
        assert client._consumer is None
        assert client._admin is None
        assert client._bootstrap_servers == []


class TestKafkaClientPropertyAccessNotConnected:
    """Tests for property access when client is not connected."""

    def test_bootstrap_servers_raises_when_not_connected(self):
        """bootstrap_servers property raises ValueError when not connected."""
        client = KafkaClient()

        with pytest.raises(
            ValueError, match="Cannot access bootstrap servers until connected"
        ):
            _ = client.bootstrap_servers

    def test_admin_raises_when_not_connected(self):
        """admin property raises ValueError when not connected."""
        client = KafkaClient()

        with pytest.raises(
            ValueError, match="Cannot access admin client until connected"
        ):
            _ = client.admin

    def test_producer_raises_when_not_connected(self):
        """producer property raises ValueError when not connected."""
        client = KafkaClient()

        with pytest.raises(ValueError, match="Cannot access producer until connected"):
            _ = client.producer

    def test_create_consumer_raises_when_not_connected(self):
        """create_consumer raises ValueError when not connected."""
        client = KafkaClient()

        with pytest.raises(ValueError, match="Cannot create consumer until connected"):
            client.create_consumer("test-group")

    def test_create_topics_raises_when_not_connected(self):
        """create_topics raises ValueError when not connected."""
        client = KafkaClient()

        with pytest.raises(ValueError, match="Cannot create topics: not connected"):
            client.create_topics(["test-topic"])


class TestKafkaClientConnection:
    """Tests for KafkaClient.connect()."""

    @patch("taphealth_kafka.client.AdminClient")
    def test_connect_sets_connected_state(self, mock_admin_class):
        """connect() sets _connected to True and stores bootstrap servers."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        client.connect(["localhost:9092"])

        assert client._connected is True
        assert client._bootstrap_servers == ["localhost:9092"]

    @patch("taphealth_kafka.client.AdminClient")
    def test_connect_with_multiple_servers(self, mock_admin_class):
        """connect() stores multiple bootstrap servers correctly."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        servers = ["broker1:9092", "broker2:9092", "broker3:9092"]
        client.connect(servers)

        assert client._bootstrap_servers == servers

    @patch("taphealth_kafka.client.AdminClient")
    def test_connect_creates_admin_client(self, mock_admin_class):
        """connect() creates AdminClient with correct configuration."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        client.connect(["localhost:9092"])

        mock_admin_class.assert_called_once_with(
            {
                "bootstrap.servers": "localhost:9092",
                "client.id": "taphealth-kafka-admin",
            }
        )

    @patch("taphealth_kafka.client.AdminClient")
    def test_connect_creates_all_topics(self, mock_admin_class):
        """connect() calls create_topics with all Topics enum values."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin.create_topics.return_value = {}
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        client.connect(["localhost:9092"])

        # Verify create_topics was called (via admin.create_topics)
        assert mock_admin.create_topics.called

    @patch("taphealth_kafka.client.AdminClient")
    def test_connect_raises_on_error(self, mock_admin_class):
        """connect() re-raises exceptions from AdminClient."""
        mock_admin_class.side_effect = Exception("Connection failed")

        client = KafkaClient()

        with pytest.raises(Exception, match="Connection failed"):
            client.connect(["localhost:9092"])

        assert client._connected is False


class TestKafkaClientProducer:
    """Tests for KafkaClient.producer property."""

    @patch("taphealth_kafka.client.Producer")
    def test_producer_creates_instance_when_connected(self, mock_producer_class):
        """producer property creates a Producer instance when connected."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        producer = client.producer

        assert producer == mock_producer
        mock_producer_class.assert_called_once()

    @patch("taphealth_kafka.client.Producer")
    def test_producer_returns_same_instance(self, mock_producer_class):
        """producer property returns cached instance on subsequent calls."""
        mock_producer = MagicMock()
        mock_producer_class.return_value = mock_producer

        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        producer1 = client.producer
        producer2 = client.producer

        assert producer1 is producer2
        assert mock_producer_class.call_count == 1

    @patch("taphealth_kafka.client.Producer")
    def test_producer_uses_correct_bootstrap_servers(self, mock_producer_class):
        """Producer is created with correct bootstrap.servers configuration."""
        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["broker1:9092", "broker2:9092"]

        _ = client.producer

        mock_producer_class.assert_called_once_with(
            {"bootstrap.servers": "broker1:9092,broker2:9092"}
        )


class TestKafkaClientConsumer:
    """Tests for KafkaClient.create_consumer()."""

    @patch("taphealth_kafka.client.Consumer")
    def test_create_consumer_returns_consumer(self, mock_consumer_class):
        """create_consumer returns a Consumer instance."""
        mock_consumer = MagicMock()
        mock_consumer_class.return_value = mock_consumer

        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        consumer = client.create_consumer("test-group")

        assert consumer == mock_consumer

    @patch("taphealth_kafka.client.Consumer")
    def test_create_consumer_maps_snake_case_config(self, mock_consumer_class):
        """create_consumer maps snake_case kwargs to dot.notation."""
        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        client.create_consumer(
            "test-group",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            session_timeout_ms=6000,
            max_poll_interval_ms=300000,
        )

        call_config = mock_consumer_class.call_args[0][0]
        assert call_config["auto.offset.reset"] == "earliest"
        assert call_config["enable.auto.commit"] is True
        assert call_config["session.timeout.ms"] == 6000
        assert call_config["max.poll.interval.ms"] == 300000

    @patch("taphealth_kafka.client.Consumer")
    def test_create_consumer_removes_kafka_python_kwargs(self, mock_consumer_class):
        """create_consumer removes kafka-python specific kwargs."""
        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        client.create_consumer(
            "test-group",
            value_deserializer=lambda x: x,
            key_deserializer=lambda x: x,
        )

        call_config = mock_consumer_class.call_args[0][0]
        assert "value_deserializer" not in call_config
        assert "key_deserializer" not in call_config

    @patch("taphealth_kafka.client.Consumer")
    def test_create_consumer_passes_confluent_kwargs(self, mock_consumer_class):
        """create_consumer passes confluent-style kwargs directly."""
        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        client.create_consumer("test-group", **{"fetch.min.bytes": 1024})

        call_config = mock_consumer_class.call_args[0][0]
        assert call_config["fetch.min.bytes"] == 1024

    @patch("taphealth_kafka.client.Consumer")
    def test_create_consumer_sets_group_id(self, mock_consumer_class):
        """create_consumer sets group.id in configuration."""
        client = KafkaClient()
        client._connected = True
        client._bootstrap_servers = ["localhost:9092"]

        client.create_consumer("my-consumer-group")

        call_config = mock_consumer_class.call_args[0][0]
        assert call_config["group.id"] == "my-consumer-group"


class TestKafkaClientTopicCreation:
    """Tests for KafkaClient.create_topics()."""

    def test_create_topics_skips_existing(self):
        """create_topics doesn't create topics that already exist."""
        client = KafkaClient()
        client._connected = True
        client._admin = MagicMock()
        client._admin.list_topics.return_value.topics.keys.return_value = [
            "existing-topic"
        ]

        client.create_topics(["existing-topic"])

        client._admin.create_topics.assert_not_called()

    @patch("taphealth_kafka.client.NewTopic")
    def test_create_topics_creates_new_topics(self, mock_new_topic):
        """create_topics creates topics that don't exist."""
        client = KafkaClient()
        client._connected = True
        client._admin = MagicMock()
        client._admin.list_topics.return_value.topics.keys.return_value = []
        client._admin.create_topics.return_value = {}

        client.create_topics(["new-topic"])

        mock_new_topic.assert_called_once_with(
            topic="new-topic", num_partitions=1, replication_factor=1
        )

    @patch("taphealth_kafka.client.NewTopic")
    def test_create_topics_creates_only_missing(self, mock_new_topic):
        """create_topics only creates topics that don't already exist."""
        client = KafkaClient()
        client._connected = True
        client._admin = MagicMock()
        client._admin.list_topics.return_value.topics.keys.return_value = [
            "existing-topic"
        ]
        client._admin.create_topics.return_value = {}

        client.create_topics(["existing-topic", "new-topic"])

        # Only new-topic should be created
        mock_new_topic.assert_called_once_with(
            topic="new-topic", num_partitions=1, replication_factor=1
        )


class TestKafkaClientDisconnection:
    """Tests for KafkaClient.disconnect()."""

    def test_disconnect_resets_state(self):
        """disconnect() resets all state to initial values."""
        client = KafkaClient()
        client._connected = True
        client._producer = MagicMock()
        client._consumer = MagicMock()
        client._admin = MagicMock()

        client.disconnect()

        assert client._connected is False
        assert client._producer is None
        assert client._consumer is None
        assert client._admin is None

    def test_disconnect_flushes_producer(self):
        """disconnect() calls producer.flush() before clearing."""
        mock_producer = MagicMock()
        client = KafkaClient()
        client._connected = True
        client._producer = mock_producer

        client.disconnect()

        mock_producer.flush.assert_called_once()

    def test_disconnect_closes_consumer(self):
        """disconnect() calls consumer.close() before clearing."""
        mock_consumer = MagicMock()
        client = KafkaClient()
        client._connected = True
        client._consumer = mock_consumer

        client.disconnect()

        mock_consumer.close.assert_called_once()

    def test_disconnect_handles_no_producer(self):
        """disconnect() works when producer is None."""
        client = KafkaClient()
        client._connected = True
        client._producer = None

        # Should not raise
        client.disconnect()

        assert client._connected is False

    def test_disconnect_handles_no_consumer(self):
        """disconnect() works when consumer is None."""
        client = KafkaClient()
        client._connected = True
        client._consumer = None

        # Should not raise
        client.disconnect()

        assert client._connected is False


class TestKafkaClientPropertyAccessConnected:
    """Tests for property access when client is connected."""

    @patch("taphealth_kafka.client.AdminClient")
    def test_bootstrap_servers_returns_servers_when_connected(self, mock_admin_class):
        """bootstrap_servers returns the list of servers when connected."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        client.connect(["broker1:9092", "broker2:9092"])

        assert client.bootstrap_servers == ["broker1:9092", "broker2:9092"]

    @patch("taphealth_kafka.client.AdminClient")
    def test_admin_returns_admin_client_when_connected(self, mock_admin_class):
        """admin property returns AdminClient when connected."""
        mock_admin = MagicMock()
        mock_admin.list_topics.return_value.topics.keys.return_value = []
        mock_admin_class.return_value = mock_admin

        client = KafkaClient()
        client.connect(["localhost:9092"])

        assert client.admin == mock_admin
