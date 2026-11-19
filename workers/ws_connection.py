from fastapi import HTTPException # type: ignore
from auth.utils import verify_token # type: ignore
from database.dynamo import get_table # type: ignore
import logging
import time

logger = logging.getLogger(__name__)

# Handles $connect and $disconnect of the websocket api
def lambda_handler(event, context):
    route = event["requestContext"]["routeKey"]
    connection_id = event["requestContext"]["connectionId"]
    collection = get_table("CONNECTIONS_TABLE")

    if route == "$connect":
        ticket = (event.get("queryStringParameters") or {}).get("ticket")
        try:
            user = verify_token(ticket, "ws")
        except (HTTPException, AttributeError):  # AttributeError is when there is no ticket at all
            logger.warning("Websocket connection refused, bad ticket")
            return {"statusCode": 401}
        # expires is used by the table to clean up connections that never said goodbye
        collection.put_item(Item={"connectionId": connection_id, "username": user.username, "expires": int(time.time()) + 7200})
        logger.info(f"Websocket connected: {user.username}")
    else:
        collection.delete_item(Key={"connectionId": connection_id})

    return {"statusCode": 200}
