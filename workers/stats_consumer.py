import boto3 # type: ignore
import json
import logging
import os

logger = logging.getLogger(__name__)

# Reads MessagePosted events from the queue and counts the messages for each user
def lambda_handler(event, context):
    collection = boto3.resource("dynamodb").Table(os.getenv("STATS_TABLE"))
    failures = []
    for record in event["Records"]:
        try:
            detail = json.loads(record["body"])["detail"]
            collection.update_item(
                Key={"username": detail["username"]},
                UpdateExpression="ADD message_count :one",
                ExpressionAttributeValues={":one": 1}
            )
        except Exception:
            logger.exception("Could not count message")
            failures.append({"itemIdentifier": record["messageId"]})  # only this one goes back on the queue
    return {"batchItemFailures": failures}
