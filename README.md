# Lambda-lounge

Latest API generated: not deployed yet

This is a serverless chat-application that works mostly as a proof of concept for creating a webserver with all it's routes be hosted as serverless instead of having a server idly running. It uses API Gateway, Lambda (FastAPI with Mangum) and DynamoDB, and the secret for the access tokens is kept in SSM Parameter Store.

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

You need the AWS CLI (configured) and SAM CLI. Run

```bash
python deploy.py
```

It creates the secret for the access tokens in SSM the first time (random, never in git), then does `sam build` and `sam deploy` and puts the new api url at the top of this README.

## Cleanup

```bash
sam delete
```
