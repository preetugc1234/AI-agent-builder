@echo off
REM AWS Backend Deployment Script for Windows

echo Starting VibeAgent Forge Backend Deployment to AWS...
echo.

REM Check if AWS CLI is installed
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not found. Please install it first.
    echo Download from: https://aws.amazon.com/cli/
    exit /b 1
)

REM Check if Docker is running
docker ps >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop.
    exit /b 1
)

REM Check required environment variables
if "%OPENROUTER_API_KEY%"=="" (
    echo ERROR: OPENROUTER_API_KEY not set
    echo Please run: set OPENROUTER_API_KEY=your-key
    exit /b 1
)

REM Set default region if not set
if "%AWS_REGION%"=="" set AWS_REGION=us-east-1

echo AWS Region: %AWS_REGION%
echo.

REM Get AWS Account ID
for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo AWS Account ID: %ACCOUNT_ID%
echo.

echo.
echo ========================================
echo Step 1: Creating AWS Infrastructure
echo ========================================
echo This will take 10-15 minutes...
echo.

aws cloudformation create-stack --stack-name vibeagent-infrastructure --template-body file://aws/cloudformation-template.yml --capabilities CAPABILITY_IAM --region %AWS_REGION%

echo Waiting for CloudFormation stack...
aws cloudformation wait stack-create-complete --stack-name vibeagent-infrastructure --region %AWS_REGION%

echo Infrastructure created successfully!
echo.

echo.
echo ========================================
echo Step 2: Creating ECR Repository
echo ========================================
echo.

aws ecr create-repository --repository-name vibeagent-backend --region %AWS_REGION% 2>nul

set ECR_URI=%ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/vibeagent-backend

echo ECR Repository: %ECR_URI%
echo.

echo.
echo ========================================
echo Step 3: Building Docker Image
echo ========================================
echo.

cd backend
docker build -t vibeagent-backend:latest .
cd ..

echo Docker image built!
echo.

echo.
echo ========================================
echo Step 4: Pushing to ECR
echo ========================================
echo.

REM Login to ECR
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %ECR_URI%

docker tag vibeagent-backend:latest %ECR_URI%:latest
docker push %ECR_URI%:latest

echo Image pushed to ECR!
echo.

echo.
echo ========================================
echo Step 5: Creating Secrets
echo ========================================
echo.

REM Get infrastructure outputs
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue" --output text --region %AWS_REGION%') do set DB_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue" --output text --region %AWS_REGION%') do set REDIS_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue" --output text --region %AWS_REGION%') do set ALB_DNS=%%i

echo Database Endpoint: %DB_ENDPOINT%
echo Redis Endpoint: %REDIS_ENDPOINT%
echo Load Balancer DNS: %ALB_DNS%
echo.

REM Create secrets (simplified - you'll need to add password retrieval)
aws secretsmanager create-secret --name vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region %AWS_REGION% 2>nul
if %ERRORLEVEL% NEQ 0 (
    aws secretsmanager update-secret --secret-id vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region %AWS_REGION%
)

echo Secrets created!
echo.

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Backend API URL: http://%ALB_DNS%
echo API Docs: http://%ALB_DNS%/docs
echo Health Check: http://%ALB_DNS%/health
echo.
echo Save this URL for Vercel frontend deployment!
echo.
echo NEXT STEPS:
echo 1. Wait 2-3 minutes for ECS service to start
echo 2. Test: curl http://%ALB_DNS%/health
echo 3. Deploy frontend on Vercel with this API URL
echo.

pause
