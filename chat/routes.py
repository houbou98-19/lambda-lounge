from fastapi import APIRouter, Depends, Response # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from auth.utils import get_current_user # type: ignore
from boto3.dynamodb.conditions import Key # type: ignore
from database.dynamo import get_table # type: ignore
from chat.models import Message # type: ignore
from auth.models import User # type: ignore
import os
import time

router = APIRouter()

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
    return {"status": "Message posted successfully"}

@router.get("/chat")
async def read_chat_page():
    return FileResponse(os.path.join("static", "chat.html"))