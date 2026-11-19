# Lambda-lounge

Latest API generated: https://58tw0bqtu2.execute-api.eu-west-1.amazonaws.com/Prod/login

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

Every push to main runs the tests and then deploys with GitHub Actions (`.github/workflows/deploy.yml`). It creates the secret for the access tokens in SSM the first time (random, never in git) and puts the new api url at the top of this README when it is done.

GitHub logs in to AWS with OIDC so there are no access keys stored anywhere. The role it uses is created once from `infra/github-oidc.yaml`:

```bash
aws cloudformation deploy --template-file infra/github-oidc.yaml --stack-name lambda-lounge-github --capabilities CAPABILITY_NAMED_IAM
```

Then add the role arn (printed as an output) as a repository variable called `AWS_ROLE_ARN`.

To deploy by hand instead you can still run `sam build` and `sam deploy`.

## Cleanup

```bash
sam delete
```
