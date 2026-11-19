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

## Events

Every new message goes through an event flow, separate from the API:

```
messages table -> DynamoDB Stream -> Lambda -> EventBridge bus -> SQS queue -> Lambda -> stats table
                                                                     \-> dead letter queue (after 3 tries)
```

The last Lambda counts messages for each user, and `GET /stats` returns the top 10. The code for the two workers is in `workers/`. Events are delivered at least once, so a count can in rare cases be too high. An alarm goes off if anything ends up in the dead letter queue. The stats stay empty when running with `python dev.py` since the fake DynamoDB has no streams.

## Live messages

New messages are pushed to the browser with a websocket api, so there is no need to refresh. Posting still goes through `POST /messages`, the websocket is only for receiving.

1. The chat page asks `GET /ws-token` (needs login) for a ticket that works for 60 seconds, and connects to the websocket api with it.
2. `workers/ws_connection.py` checks the ticket and saves the connection in the connections table. The ticket has its own scope so it can't be used to log in.
3. When a message is posted it goes through the event flow above, and `workers/broadcaster.py` sends it to every saved connection.

If the websocket is down the page goes back to asking for messages every 5 seconds, and it tries to connect again. With `python dev.py` there is no websocket so it always polls.

## Monitoring

- Logs are JSON in the log group `/lambda-lounge/api` and are kept for 14 days.
- X-Ray tracing is on for both API Gateway and Lambda.
- The API is throttled to 5 requests per second (burst 10).
- CloudWatch alarms for Lambda errors, API 5xx and slow requests, plus a 5 USD monthly budget alert, all send mail to an SNS topic. To get the mails set the repository variable `ALERT_EMAIL` and confirm the subscription mail from AWS:

```bash
gh variable set ALERT_EMAIL --body "you@example.com"
```

## Cleanup

```bash
sam delete
```
