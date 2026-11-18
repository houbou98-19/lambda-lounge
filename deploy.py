# Builds and deploys the stack, then puts the api url in the README: python deploy.py
import boto3 # type: ignore
import re
import secrets
import shutil
import subprocess

STACK_NAME = "lambda-lounge"
REGION = "eu-west-1"
SECRET_NAME = "/lambda-lounge/secret-key"

# The secret for the access tokens is created once, it is never in git
ssm = boto3.client("ssm", region_name=REGION)
try:
    ssm.get_parameter(Name=SECRET_NAME)
except ssm.exceptions.ParameterNotFound:
    ssm.put_parameter(Name=SECRET_NAME, Value=secrets.token_urlsafe(48), Type="SecureString")
    print("Created " + SECRET_NAME)

sam = shutil.which("sam")
subprocess.run([sam, "build"], check=True)
subprocess.run([sam, "deploy", "--stack-name", STACK_NAME, "--region", REGION, "--resolve-s3",
                "--capabilities", "CAPABILITY_IAM", "--no-confirm-changeset", "--no-fail-on-empty-changeset"], check=True)

cloudformation = boto3.client("cloudformation", region_name=REGION)
outputs = cloudformation.describe_stacks(StackName=STACK_NAME)["Stacks"][0]["Outputs"]
url = next(o["OutputValue"] for o in outputs if o["OutputKey"] == "ApiUrl")

with open("README.md", encoding="utf-8") as f:
    readme = f.read()
readme = re.sub(r"Latest API generated: .*", "Latest API generated: " + url, readme)
with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)
print("README updated with " + url)
