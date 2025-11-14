@echo off
REM Check CloudFormation Stack Errors

echo Checking what failed...
echo.

REM Load credentials
if not exist credentials.txt (
    echo ERROR: credentials.txt not found!
    pause
    exit /b 1
)

for /f "tokens=1,2 delims==" %%a in (credentials.txt) do (
    set %%a=%%b
)

aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region us-east-1

echo Getting failed resources...
echo.

aws cloudformation describe-stack-events --stack-name vibeagent-infrastructure --region us-east-1 --output json > stack-events.json

echo Saved to stack-events.json
echo.
echo Opening file...

notepad stack-events.json

pause
