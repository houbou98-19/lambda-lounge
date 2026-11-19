import json
import boto3 # type: ignore
import pytest # type: ignore
from unittest.mock import patch
from workers import stats_consumer, stream_processor

def stream_record(event_name, username="alice"):
    return {"eventName": event_name, "dynamodb": {"NewImage": {"room": {"S": "general"}, "username": {"S": username}, "timestamp": {"N": "123"}}}}

def queue_record(message_id, username="alice"):
    return {"messageId": message_id, "body": json.dumps({"detail": {"username": username}})}

def test_stream_processor_only_publishes_inserts():
    with patch("workers.stream_processor.boto3.client") as client:
        client.return_value.put_events.return_value = {"FailedEntryCount": 0}
        stream_processor.lambda_handler({"Records": [stream_record("INSERT"), stream_record("MODIFY"), stream_record("REMOVE")]}, None)
    entries = client.return_value.put_events.call_args.kwargs["Entries"]
    assert len(entries) == 1
    assert entries[0]["DetailType"] == "MessagePosted"
    assert json.loads(entries[0]["Detail"])["username"] == "alice"

def test_stream_processor_sends_in_batches_of_ten():
    with patch("workers.stream_processor.boto3.client") as client:
        client.return_value.put_events.return_value = {"FailedEntryCount": 0}
        stream_processor.lambda_handler({"Records": [stream_record("INSERT") for _ in range(25)]}, None)
    assert client.return_value.put_events.call_count == 3

def test_stream_processor_raises_when_events_fail():
    with patch("workers.stream_processor.boto3.client") as client:
        client.return_value.put_events.return_value = {"FailedEntryCount": 1}
        with pytest.raises(Exception):
            stream_processor.lambda_handler({"Records": [stream_record("INSERT")]}, None)

def test_stats_consumer_counts_messages_per_user():
    result = stats_consumer.lambda_handler({"Records": [queue_record("1"), queue_record("2"), queue_record("3", "bob")]}, None)
    assert result == {"batchItemFailures": []}
    table = boto3.resource("dynamodb").Table("stats")
    assert table.get_item(Key={"username": "alice"})["Item"]["message_count"] == 2
    assert table.get_item(Key={"username": "bob"})["Item"]["message_count"] == 1

def test_stats_consumer_only_fails_the_broken_record():
    broken = {"messageId": "bad", "body": "not json"}
    result = stats_consumer.lambda_handler({"Records": [queue_record("1"), broken]}, None)
    assert result == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
