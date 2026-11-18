# Lambda-lounge

This is a serverless chat-application that works mostly as a proof of concept for creating a webserver with all it's routes be hosted as serverless instead of having a server idly running. It uses API Gateway, Lambda (FastAPI with Mangum) and DynamoDB, and the secret for the access tokens is generated in Secrets Manager.

It started out as my degree project [chatapp-serverless](https://github.com/houbou98-19/chatapp-serverless) (tag `thesis-final`) which used MongoDB Atlas. This version uses DynamoDB instead.

## Local development (no Docker needed)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
python dev.py                 # http://127.0.0.1:8000/login (fake DynamoDB, data is lost when you stop it)
pytest
```

## Deploy to AWS

You need the AWS CLI (configured) and SAM CLI. The stack creates its own tables and secret so there is nothing to put in SSM anymore.

```bash
sam build --use-container
sam deploy --guided      # first time; later just `sam deploy`
```

The API url is printed as an output when it is done.

## Cleanup

```bash
sam delete
```
