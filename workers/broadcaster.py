import boto3 # type: ignore
import json
import logging
import os
from database.dynamo import get_table # type: ignore

logger = logging.getLogger(__name__)

# Sends a new message to everyone who is connected with the websocket api
def lambda_handler(event, context):
    detail = event["detail"]
    data = json.dumps({"username": detail["username"], "messagecontent": detail["messagecontent"], "timestamp": detail["timestamp"]}).encode("utf-8")

    collection = get_table("CONNECTIONS_TABLE")
    client = boto3.client("apigatewaymanagementapi", endpoint_url=os.getenv("WEBSOCKET_ENDPOINT"))
    sent = 0
    for connection in collection.scan()["Items"]:
        try:
            client.post_to_connection(ConnectionId=connection["connectionId"], Data=data)
            sent += 1
        except client.exceptions.GoneException:
            collection.delete_item(Key={"connectionId": connection["connectionId"]})  # they hung up
    logger.info(f"Message sent to {sent} connections")
