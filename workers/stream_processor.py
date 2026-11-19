import boto3 # type: ignore
import json
import logging
import os

logger = logging.getLogger(__name__)

# Gets new rows from the messages table and puts a MessagePosted event on the event bus
def lambda_handler(event, context):
    entries = []
    for record in event["Records"]:
        if record["eventName"] != "INSERT":
            continue
        message = record["dynamodb"]["NewImage"]
        detail = {"room": message["room"]["S"], "username": message["username"]["S"], "timestamp": message["timestamp"]["N"]}
        entries.append({
            "Source": "lambda-lounge.chat",
            "DetailType": "MessagePosted",
            "Detail": json.dumps(detail),
            "EventBusName": os.getenv("EVENT_BUS")
        })

    client = boto3.client("events")
    for i in range(0, len(entries), 10):  # put_events takes 10 entries at most
        response = client.put_events(Entries=entries[i:i + 10])
        if response["FailedEntryCount"] > 0:
            raise Exception("Could not put all events on the bus")  # makes the stream retry the batch
    logger.info(f"Published {len(entries)} events")
