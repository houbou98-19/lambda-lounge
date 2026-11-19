import os
from datetime import datetime, timedelta
from jose import jwt # type: ignore
from fastapi import HTTPException, status, Request # type: ignore
from auth.models import User
import bcrypt # type: ignore
import boto3 # type: ignore
from functools import lru_cache

ALGORITHM = "HS256"

@lru_cache(maxsize=1)
def get_secret_key():
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        client = boto3.client("ssm")
        secret_key = client.get_parameter(Name=os.getenv("SECRET_PARAMETER"), WithDecryption=True)["Parameter"]["Value"]
    return secret_key

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_secret_key(), algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, scope: str = None):  # normal login tokens have no scope, websocket tickets have "ws"
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or payload.get("scope") != scope:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return User(username=username)
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(request: Request):  # Checks if user is authenticated and returns user object
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return verify_token(token)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
