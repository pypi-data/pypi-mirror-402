"""
Tests for KafkaProducer.

Test Coverage:
=============

Initialization
--------------
- test_init_stores_client: __init__ stores client reference
- test_init_accesses_producer_from_client: __init__ accesses client.producer

Topic Property
--------------
- test_topic_property_returns_correct_topic: Abstract topic property works correctly

Send Method - Basic Functionality
---------------------------------
- test_send_serializes_data_to_json: send() serializes dict to JSON
- test_send_encodes_as_utf8: send() encodes JSON string as UTF-8 bytes
- test_send_produces_to_correct_topic: send() uses topic.value as topic name
- test_send_flushes_after_produce: send() calls flush with timeout=10
- test_send_sets_delivery_callback: send() passes _delivery_callback to produce

Send Method - Error Handling
----------------------------
- test_send_raises_on_flush_timeout: send() raises when flush returns > 0
- test_send_raises_on_delivery_error: send() raises when delivery callback sets error
- test_send_resets_delivery_error_before_send: send() clears _delivery_error before sending
- test_send_logs_error_on_exception: send() logs error before re-raising

Delivery Callback
-----------------
- test_delivery_callback_sets_error_on_failure: _delivery_callback sets _delivery_error
- test_delivery_callback_logs_error_on_failure: _delivery_callback logs error message
- test_delivery_callback_no_error_on_success: _delivery_callback doesn't set error on success

JSON Serializer
---------------
- test_json_serializer_handles_dict_objects: Serializes objects with __dict__
- test_json_serializer_handles_datetime: Serializes objects with isoformat()
- test_json_serializer_raises_for_non_serializable: Raises TypeError for unknown types
- test_send_uses_custom_serializer: send() uses _json_serializer for non-standard types
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from taphealth_kafka import KafkaProducer, Topics


class SampleProducer(KafkaProducer):
    """Concrete implementation of KafkaProducer for testing."""

    @property
    def topic(self):
        return Topics.WEEKLY_PLAN_CREATED


@pytest.fixture
def mock_client():
    """Create a mock client with producer configured."""
    client = MagicMock()
    mock_producer = MagicMock()
    mock_producer.flush.return_value = 0  # No remaining messages
    client.producer = mock_producer
    return client


class TestKafkaProducerInitialization:
    """Tests for KafkaProducer initialization."""

    def test_init_stores_client(self, mock_client):
        """__init__ stores client reference."""
        producer = SampleProducer(mock_client)

        assert producer.client == mock_client

    def test_init_accesses_producer_from_client(self, mock_client):
        """__init__ accesses client.producer."""
        producer = SampleProducer(mock_client)

        assert producer._producer == mock_client.producer

    def test_init_sets_delivery_error_to_none(self, mock_client):
        """__init__ sets _delivery_error to None."""
        producer = SampleProducer(mock_client)

        assert producer._delivery_error is None


class TestKafkaProducerTopicProperty:
    """Tests for KafkaProducer.topic property."""

    def test_topic_property_returns_correct_topic(self, mock_client):
        """topic property returns the correct Topics enum value."""
        producer = SampleProducer(mock_client)

        assert producer.topic == Topics.WEEKLY_PLAN_CREATED

    def test_topic_is_topics_enum(self, mock_client):
        """topic property returns a Topics enum member."""
        producer = SampleProducer(mock_client)

        assert isinstance(producer.topic, Topics)


class TestKafkaProducerSendBasic:
    """Tests for KafkaProducer.send() basic functionality."""

    def test_send_serializes_data_to_json(self, mock_client):
        """send() serializes dict to JSON."""
        producer = SampleProducer(mock_client)

        test_data = {"planId": "123", "userId": "456"}
        producer.send(test_data)

        # Verify produce was called
        mock_client.producer.produce.assert_called_once()
        call_kwargs = mock_client.producer.produce.call_args[1]

        # Verify the data was serialized correctly
        assert json.loads(call_kwargs["value"].decode("utf-8")) == test_data

    def test_send_encodes_as_utf8(self, mock_client):
        """send() encodes JSON string as UTF-8 bytes."""
        producer = SampleProducer(mock_client)

        producer.send({"key": "value"})

        call_kwargs = mock_client.producer.produce.call_args[1]
        assert isinstance(call_kwargs["value"], bytes)

    def test_send_produces_to_correct_topic(self, mock_client):
        """send() uses topic.value as topic name."""
        producer = SampleProducer(mock_client)

        producer.send({"test": "data"})

        call_kwargs = mock_client.producer.produce.call_args[1]
        assert call_kwargs["topic"] == "weekly-plan-created"

    def test_send_flushes_after_produce(self, mock_client):
        """send() calls flush with timeout=10."""
        producer = SampleProducer(mock_client)

        producer.send({"test": "data"})

        mock_client.producer.flush.assert_called_once_with(timeout=10)

    def test_send_sets_delivery_callback(self, mock_client):
        """send() passes _delivery_callback to produce."""
        producer = SampleProducer(mock_client)

        producer.send({"test": "data"})

        call_kwargs = mock_client.producer.produce.call_args[1]
        assert call_kwargs["callback"] == producer._delivery_callback

    def test_send_handles_nested_dict(self, mock_client):
        """send() correctly serializes nested dictionaries."""
        producer = SampleProducer(mock_client)

        test_data = {
            "user": {"id": "123", "name": "Test User"},
            "items": [1, 2, 3],
        }
        producer.send(test_data)

        call_kwargs = mock_client.producer.produce.call_args[1]
        assert json.loads(call_kwargs["value"].decode("utf-8")) == test_data

    def test_send_handles_list_data(self, mock_client):
        """send() correctly serializes list data."""
        producer = SampleProducer(mock_client)

        test_data = [{"id": 1}, {"id": 2}]
        producer.send(test_data)

        call_kwargs = mock_client.producer.produce.call_args[1]
        assert json.loads(call_kwargs["value"].decode("utf-8")) == test_data


class TestKafkaProducerSendErrors:
    """Tests for KafkaProducer.send() error handling."""

    def test_send_raises_on_flush_timeout(self, mock_client):
        """send() raises when flush returns > 0 (messages remaining)."""
        mock_client.producer.flush.return_value = 1  # 1 message remaining

        producer = SampleProducer(mock_client)

        with pytest.raises(Exception, match="Failed to deliver 1 message"):
            producer.send({"test": "data"})

    def test_send_raises_on_delivery_error(self, mock_client):
        """send() raises when delivery callback sets error."""
        producer = SampleProducer(mock_client)

        # Simulate delivery callback being called with an error
        def set_error_callback(*args, **kwargs):
            callback = kwargs.get("callback")
            if callback:
                callback("Delivery error", None)

        mock_client.producer.produce.side_effect = set_error_callback

        with pytest.raises(Exception, match="Delivery failed"):
            producer.send({"test": "data"})

    def test_send_resets_delivery_error_before_send(self, mock_client):
        """send() clears _delivery_error before sending."""
        producer = SampleProducer(mock_client)
        producer._delivery_error = Exception("Previous error")

        producer.send({"test": "data"})

        # If we got here without exception, error was cleared
        # (since delivery was successful)

    @patch("taphealth_kafka.producer.logger")
    def test_send_logs_error_on_exception(self, mock_logger, mock_client):
        """send() logs error before re-raising."""
        mock_client.producer.produce.side_effect = Exception("Produce failed")

        producer = SampleProducer(mock_client)

        with pytest.raises(Exception):
            producer.send({"test": "data"})

        mock_logger.error.assert_called()


class TestKafkaProducerDeliveryCallback:
    """Tests for KafkaProducer._delivery_callback()."""

    def test_delivery_callback_sets_error_on_failure(self, mock_client):
        """_delivery_callback sets _delivery_error when err is not None."""
        producer = SampleProducer(mock_client)
        error = MagicMock()

        producer._delivery_callback(error, None)

        assert producer._delivery_error == error

    @patch("taphealth_kafka.producer.logger")
    def test_delivery_callback_logs_error_on_failure(self, mock_logger, mock_client):
        """_delivery_callback logs error message when err is not None."""
        producer = SampleProducer(mock_client)
        error = MagicMock()
        error.__str__ = MagicMock(return_value="Delivery failed")

        producer._delivery_callback(error, None)

        mock_logger.error.assert_called()

    def test_delivery_callback_no_error_on_success(self, mock_client):
        """_delivery_callback doesn't set error when err is None."""
        producer = SampleProducer(mock_client)
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0

        producer._delivery_callback(None, mock_msg)

        assert producer._delivery_error is None

    @patch("taphealth_kafka.producer.logger")
    def test_delivery_callback_logs_debug_on_success(self, mock_logger, mock_client):
        """_delivery_callback logs debug message on successful delivery."""
        producer = SampleProducer(mock_client)
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.partition.return_value = 0

        producer._delivery_callback(None, mock_msg)

        mock_logger.debug.assert_called()


class TestKafkaProducerJsonSerializer:
    """Tests for KafkaProducer._json_serializer()."""

    def test_json_serializer_handles_dict_objects(self, mock_client):
        """_json_serializer serializes objects with __dict__."""
        producer = SampleProducer(mock_client)

        class CustomObject:
            def __init__(self):
                self.id = 123
                self.name = "test"

        obj = CustomObject()
        result = producer._json_serializer(obj)

        assert result == {"id": 123, "name": "test"}

    def test_json_serializer_handles_datetime(self, mock_client):
        """_json_serializer serializes objects with isoformat()."""
        producer = SampleProducer(mock_client)

        dt = datetime(2025, 1, 15, 10, 30, 0)
        result = producer._json_serializer(dt)

        assert result == "2025-01-15T10:30:00"

    def test_json_serializer_raises_for_non_serializable(self, mock_client):
        """_json_serializer raises TypeError for unknown types."""
        producer = SampleProducer(mock_client)

        # Use a class with __slots__ to prevent __dict__
        class NonSerializable:
            __slots__ = ()

        obj = NonSerializable()

        with pytest.raises(TypeError, match="not serializable"):
            producer._json_serializer(obj)

    def test_send_uses_custom_serializer(self, mock_client):
        """send() uses _json_serializer for non-standard types."""
        producer = SampleProducer(mock_client)

        dt = datetime(2025, 1, 15, 10, 30, 0)
        test_data = {"timestamp": dt, "value": 42}

        producer.send(test_data)

        call_kwargs = mock_client.producer.produce.call_args[1]
        result = json.loads(call_kwargs["value"].decode("utf-8"))
        assert result == {"timestamp": "2025-01-15T10:30:00", "value": 42}

    def test_send_uses_custom_serializer_for_nested_objects(self, mock_client):
        """send() uses _json_serializer for nested custom objects."""
        producer = SampleProducer(mock_client)

        class UserData:
            def __init__(self):
                self.id = "user-123"
                self.email = "test@example.com"

        test_data = {"user": UserData(), "action": "login"}

        producer.send(test_data)

        call_kwargs = mock_client.producer.produce.call_args[1]
        result = json.loads(call_kwargs["value"].decode("utf-8"))
        assert result == {
            "user": {"id": "user-123", "email": "test@example.com"},
            "action": "login",
        }
