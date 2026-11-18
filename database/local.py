import boto3 # type: ignore
import os

def create_tables():
    dynamodb = boto3.resource("dynamodb")
    dynamodb.create_table(
        TableName=os.getenv("USERS_TABLE"),
        KeySchema=[{"AttributeName": "username", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "username", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST"
    )
    dynamodb.create_table(
        TableName=os.getenv("MESSAGES_TABLE"),
        KeySchema=[
            {"AttributeName": "room", "KeyType": "HASH"},
            {"AttributeName": "timestamp", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "room", "AttributeType": "S"},
            {"AttributeName": "timestamp", "AttributeType": "N"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
