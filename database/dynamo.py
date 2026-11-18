import boto3 # type: ignore
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def connect_to_dynamodb():
    return boto3.resource("dynamodb")

def get_table(table_name: str):
    return connect_to_dynamodb().Table(os.getenv(table_name))
