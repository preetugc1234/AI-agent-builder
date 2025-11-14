@echo off
REM Setup AWS Credentials for Deployment

echo ========================================
echo AWS Credentials Setup
echo ========================================
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not installed
    echo.
    echo Please install from: https://aws.amazon.com/cli/
    echo After installing, run this script again.
    pause
    exit /b 1
)

echo AWS CLI found!
echo.
echo Please enter your AWS credentials:
echo (Get these from AWS Console ^> IAM ^> Users ^> Security Credentials)
echo.

set /p AWS_ACCESS_KEY=Enter AWS Access Key ID:
set /p AWS_SECRET_KEY=Enter AWS Secret Access Key:
set /p AWS_REGION=Enter AWS Region (default: us-east-1):

if "%AWS_REGION%"=="" set AWS_REGION=us-east-1

echo.
echo Configuring AWS CLI...

aws configure set aws_access_key_id %AWS_ACCESS_KEY%
aws configure set aws_secret_access_key %AWS_SECRET_KEY%
aws configure set default.region %AWS_REGION%
aws configure set default.output json

echo.
echo Testing AWS credentials...
aws sts get-caller-identity

if %ERRORLEVEL% EQU 0 (
    echo.
    echo SUCCESS! AWS credentials configured correctly.
    echo.
    echo Now enter your OpenRouter API Key:
    echo (Get from https://openrouter.ai/)
    echo.
    set /p OPENROUTER_KEY=Enter OpenRouter API Key:

    REM Save to environment
    setx OPENROUTER_API_KEY "%OPENROUTER_KEY%"
    set OPENROUTER_API_KEY=%OPENROUTER_KEY%

    echo.
    echo ========================================
    echo Configuration Complete!
    echo ========================================
    echo.
    echo AWS Region: %AWS_REGION%
    echo OpenRouter API Key: Set
    echo.
    echo You can now run: deploy-backend.bat
    echo.
) else (
    echo.
    echo ERROR: AWS credentials are invalid.
    echo Please check your Access Key and Secret Key.
)

pause
