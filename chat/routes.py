from fastapi import APIRouter, Depends, Response # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from auth.utils import get_current_user # type: ignore
from boto3.dynamodb.conditions import Key # type: ignore
from database.dynamo import get_table # type: ignore
from chat.models import Message # type: ignore
from auth.models import User # type: ignore
import logging
import os
import time

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/messages")
async def get_messages(response: Response, current_user: User = Depends(get_current_user)):
    collection = get_table("MESSAGES_TABLE")
    response = collection.query(KeyConditionExpression=Key("room").eq("general"), ScanIndexForward=False, Limit=100)
    messages = [{"username": m["username"], "messagecontent": m["messagecontent"]} for m in reversed(response["Items"])]
    return JSONResponse(content=messages)

@router.post("/messages")
async def post_message(message: Message, current_user: User = Depends(get_current_user)):
    collection = get_table("MESSAGES_TABLE")
    collection.put_item(Item={"room": "general", "timestamp": time.time_ns(), "username": current_user.username, "messagecontent": message.content})
    logger.info(f"Message posted by: {current_user.username}")
    return {"status": "Message posted successfully"}

@router.get("/stats")
async def get_stats(current_user: User = Depends(get_current_user)):
    collection = get_table("STATS_TABLE")
    users = collection.scan()["Items"]
    stats = [{"username": u["username"], "messages": int(u["message_count"])} for u in users]
    stats.sort(key=lambda s: s["messages"], reverse=True)
    return JSONResponse(content=stats[:10])

@router.get("/chat")
async def read_chat_page():
    return FileResponse(os.path.join("static", "chat.html"))