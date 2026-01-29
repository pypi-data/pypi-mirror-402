"""
Tests for KafkaConsumer.

Test Coverage:
=============

Initialization
--------------
- test_init_stores_client: __init__ stores client reference

Abstract Properties
-------------------
- test_topic_property_returns_correct_topic: topic property returns Topics enum
- test_group_id_property_returns_correct_group: group_id returns string

on_message Method
-----------------
- test_on_message_receives_data: on_message receives parsed data
- test_on_message_receives_message: on_message receives raw message object

ensure_topics_exist Method
--------------------------
- test_ensure_topics_exist_calls_create_topics: Calls client.create_topics with topic value
- test_ensure_topics_exist_uses_topic_value: Uses topic.value not topic enum

consume Method - Setup
----------------------
- test_consume_calls_ensure_topics_exist: consume() calls ensure_topics_exist first
- test_consume_creates_consumer_with_group_id: consume() creates consumer with correct group_id
- test_consume_creates_consumer_with_auto_offset_reset: Uses 'earliest' auto_offset_reset
- test_consume_creates_consumer_with_auto_commit: Enables auto commit
- test_consume_subscribes_to_topic: consume() subscribes to correct topic

consume Method - Message Handling
---------------------------------
- test_consume_handles_none_message: Continues loop when poll returns None
- test_consume_handles_message_error: Logs error and continues when message.error()
- test_consume_deserializes_json_message: Deserializes JSON message and calls on_message
- test_consume_handles_json_decode_error: Logs error and continues on invalid JSON
- test_consume_handles_none_message_value: Passes None data when message value is None
- test_consume_passes_message_to_on_message: Passes raw message to on_message

consume Method - Termination
----------------------------
- test_consume_handles_keyboard_interrupt: Exits gracefully on KeyboardInterrupt
- test_consume_closes_consumer_in_finally: Always closes consumer in finally block
- test_consume_handles_general_exception: Logs error on general exception
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from taphealth_kafka import KafkaConsumer, Topics


class SampleConsumer(KafkaConsumer):
    """Concrete implementation of KafkaConsumer for testing."""

    def __init__(self, client):
        super().__init__(client)
        self.received_messages = []
        self.received_raw_messages = []

    @property
    def topic(self):
        return Topics.WEEKLY_PLAN_CREATED

    @property
    def group_id(self):
        return "test-group"

    def on_message(self, data, message):
        self.received_messages.append(data)
        self.received_raw_messages.append(message)


@pytest.fixture
def mock_client():
    """Create a mock client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_consumer():
    """Create a mock consumer for testing consume()."""
    consumer = MagicMock()
    return consumer


class TestKafkaConsumerInitialization:
    """Tests for KafkaConsumer initialization."""

    def test_init_stores_client(self, mock_client):
        """__init__ stores client reference."""
        consumer = SampleConsumer(mock_client)

        assert consumer.client == mock_client


class TestKafkaConsumerAbstractProperties:
    """Tests for KafkaConsumer abstract properties."""

    def test_topic_property_returns_correct_topic(self, mock_client):
        """topic property returns the correct Topics enum value."""
        consumer = SampleConsumer(mock_client)

        assert consumer.topic == Topics.WEEKLY_PLAN_CREATED

    def test_topic_is_topics_enum(self, mock_client):
        """topic property returns a Topics enum member."""
        consumer = SampleConsumer(mock_client)

        assert isinstance(consumer.topic, Topics)

    def test_group_id_property_returns_correct_group(self, mock_client):
        """group_id property returns the correct string."""
        consumer = SampleConsumer(mock_client)

        assert consumer.group_id == "test-group"

    def test_group_id_is_string(self, mock_client):
        """group_id property returns a string."""
        consumer = SampleConsumer(mock_client)

        assert isinstance(consumer.group_id, str)


class TestKafkaConsumerOnMessage:
    """Tests for KafkaConsumer.on_message()."""

    def test_on_message_receives_data(self, mock_client):
        """on_message receives parsed data as first argument."""
        consumer = SampleConsumer(mock_client)

        test_data = {"planId": "123", "userId": "456"}
        mock_message = MagicMock()

        consumer.on_message(test_data, mock_message)

        assert len(consumer.received_messages) == 1
        assert consumer.received_messages[0] == test_data

    def test_on_message_receives_message(self, mock_client):
        """on_message receives raw message as second argument."""
        consumer = SampleConsumer(mock_client)

        test_data = {"planId": "123"}
        mock_message = MagicMock()

        consumer.on_message(test_data, mock_message)

        assert len(consumer.received_raw_messages) == 1
        assert consumer.received_raw_messages[0] == mock_message

    def test_on_message_handles_none_data(self, mock_client):
        """on_message can receive None as data."""
        consumer = SampleConsumer(mock_client)

        consumer.on_message(None, MagicMock())

        assert len(consumer.received_messages) == 1
        assert consumer.received_messages[0] is None


class TestKafkaConsumerEnsureTopicsExist:
    """Tests for KafkaConsumer.ensure_topics_exist()."""

    def test_ensure_topics_exist_calls_create_topics(self, mock_client):
        """ensure_topics_exist calls client.create_topics."""
        consumer = SampleConsumer(mock_client)

        consumer.ensure_topics_exist()

        mock_client.create_topics.assert_called_once()

    def test_ensure_topics_exist_uses_topic_value(self, mock_client):
        """ensure_topics_exist uses topic.value (string) not topic enum."""
        consumer = SampleConsumer(mock_client)

        consumer.ensure_topics_exist()

        mock_client.create_topics.assert_called_once_with(["weekly-plan-created"])

    @patch("taphealth_kafka.consumer.logger")
    def test_ensure_topics_exist_logs_info(self, mock_logger, mock_client):
        """ensure_topics_exist logs info message."""
        consumer = SampleConsumer(mock_client)

        consumer.ensure_topics_exist()

        mock_logger.info.assert_called()


class TestKafkaConsumerConsumeSetup:
    """Tests for KafkaConsumer.consume() setup behavior."""

    def test_consume_calls_ensure_topics_exist(self, mock_client, mock_consumer):
        """consume() calls ensure_topics_exist first."""
        mock_client.create_consumer.return_value = mock_consumer
        # Make poll raise KeyboardInterrupt to exit the loop
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_client.create_topics.assert_called_once()

    def test_consume_creates_consumer_with_group_id(self, mock_client, mock_consumer):
        """consume() creates consumer with correct group_id."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_client.create_consumer.assert_called_once()
        call_kwargs = mock_client.create_consumer.call_args
        assert call_kwargs[1]["group_id"] == "test-group"

    def test_consume_creates_consumer_with_auto_offset_reset(
        self, mock_client, mock_consumer
    ):
        """consume() creates consumer with auto_offset_reset='earliest'."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        call_kwargs = mock_client.create_consumer.call_args
        assert call_kwargs[1]["auto_offset_reset"] == "earliest"

    def test_consume_creates_consumer_with_auto_commit(
        self, mock_client, mock_consumer
    ):
        """consume() creates consumer with enable_auto_commit=True."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        call_kwargs = mock_client.create_consumer.call_args
        assert call_kwargs[1]["enable_auto_commit"] is True

    def test_consume_subscribes_to_topic(self, mock_client, mock_consumer):
        """consume() subscribes consumer to correct topic."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_consumer.subscribe.assert_called_once_with(["weekly-plan-created"])


class TestKafkaConsumerConsumeMessageHandling:
    """Tests for KafkaConsumer.consume() message handling."""

    def test_consume_handles_none_message(self, mock_client, mock_consumer):
        """consume() continues loop when poll returns None (timeout)."""
        mock_client.create_consumer.return_value = mock_consumer
        # First poll returns None, second raises KeyboardInterrupt
        mock_consumer.poll.side_effect = [None, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        assert mock_consumer.poll.call_count == 2
        assert len(consumer.received_messages) == 0

    def test_consume_handles_message_error(self, mock_client, mock_consumer):
        """consume() logs error and continues when message.error() returns True."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_message = MagicMock()
        mock_message.error.return_value = MagicMock()  # Truthy error
        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        with patch("taphealth_kafka.consumer.logger") as mock_logger:
            consumer.consume()
            mock_logger.error.assert_called()

        assert len(consumer.received_messages) == 0

    def test_consume_deserializes_json_message(self, mock_client, mock_consumer):
        """consume() deserializes JSON message and calls on_message."""
        mock_client.create_consumer.return_value = mock_consumer

        test_data = {"planId": "123", "userId": "456"}
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = json.dumps(test_data).encode("utf-8")
        mock_message.partition.return_value = 0

        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        assert len(consumer.received_messages) == 1
        assert consumer.received_messages[0] == test_data

    def test_consume_handles_json_decode_error(self, mock_client, mock_consumer):
        """consume() logs error and continues on invalid JSON."""
        mock_client.create_consumer.return_value = mock_consumer

        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = b"not valid json"

        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        with patch("taphealth_kafka.consumer.logger") as mock_logger:
            consumer.consume()
            # Should log JSON decode error
            mock_logger.error.assert_called()

        assert len(consumer.received_messages) == 0

    def test_consume_handles_none_message_value(self, mock_client, mock_consumer):
        """consume() passes None data when message value is None."""
        mock_client.create_consumer.return_value = mock_consumer

        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = None
        mock_message.partition.return_value = 0

        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        assert len(consumer.received_messages) == 1
        assert consumer.received_messages[0] is None

    def test_consume_passes_message_to_on_message(self, mock_client, mock_consumer):
        """consume() passes raw message to on_message."""
        mock_client.create_consumer.return_value = mock_consumer

        test_data = {"test": "data"}
        mock_message = MagicMock()
        mock_message.error.return_value = None
        mock_message.value.return_value = json.dumps(test_data).encode("utf-8")
        mock_message.partition.return_value = 0

        mock_consumer.poll.side_effect = [mock_message, KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        assert len(consumer.received_raw_messages) == 1
        assert consumer.received_raw_messages[0] == mock_message

    def test_consume_polls_with_timeout(self, mock_client, mock_consumer):
        """consume() polls with 1.0 second timeout."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_consumer.poll.assert_called_with(timeout=1.0)


class TestKafkaConsumerConsumeTermination:
    """Tests for KafkaConsumer.consume() termination behavior."""

    def test_consume_handles_keyboard_interrupt(self, mock_client, mock_consumer):
        """consume() exits gracefully on KeyboardInterrupt."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        # Should not raise
        consumer.consume()

        mock_consumer.close.assert_called_once()

    @patch("taphealth_kafka.consumer.logger")
    def test_consume_logs_keyboard_interrupt(
        self, mock_logger, mock_client, mock_consumer
    ):
        """consume() logs info on KeyboardInterrupt."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        # Should log keyboard interrupt message
        assert any(
            "keyboard interrupt" in str(c).lower()
            for c in mock_logger.info.call_args_list
        )

    def test_consume_closes_consumer_in_finally(self, mock_client, mock_consumer):
        """consume() always closes consumer in finally block."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_consumer.close.assert_called_once()

    def test_consume_closes_consumer_on_exception(self, mock_client, mock_consumer):
        """consume() closes consumer even when exception occurs."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = Exception("Unexpected error")

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_consumer.close.assert_called_once()

    @patch("taphealth_kafka.consumer.logger")
    def test_consume_logs_general_exception(
        self, mock_logger, mock_client, mock_consumer
    ):
        """consume() logs error on general exception."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = Exception("Unexpected error")

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        mock_logger.error.assert_called()

    @patch("taphealth_kafka.consumer.logger")
    def test_consume_logs_consumer_closed(
        self, mock_logger, mock_client, mock_consumer
    ):
        """consume() logs info when consumer is closed."""
        mock_client.create_consumer.return_value = mock_consumer
        mock_consumer.poll.side_effect = KeyboardInterrupt()

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        # Should log consumer closed message
        assert any("closed" in str(c).lower() for c in mock_logger.info.call_args_list)


class TestKafkaConsumerMultipleMessages:
    """Tests for consuming multiple messages."""

    def test_consume_processes_multiple_messages(self, mock_client, mock_consumer):
        """consume() processes multiple messages before interrupt."""
        mock_client.create_consumer.return_value = mock_consumer

        messages = []
        for i in range(3):
            mock_msg = MagicMock()
            mock_msg.error.return_value = None
            mock_msg.value.return_value = json.dumps({"id": i}).encode("utf-8")
            mock_msg.partition.return_value = 0
            messages.append(mock_msg)

        mock_consumer.poll.side_effect = messages + [KeyboardInterrupt()]

        consumer = SampleConsumer(mock_client)

        consumer.consume()

        assert len(consumer.received_messages) == 3
        assert consumer.received_messages == [{"id": 0}, {"id": 1}, {"id": 2}]
