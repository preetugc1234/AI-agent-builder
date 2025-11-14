@echo off
REM VibeAgent Forge - Automated Deployment
REM All credentials are pre-configured

echo ========================================
echo VIBEAGENT FORGE - AUTOMATED DEPLOYMENT
echo ========================================
echo.

REM Load credentials from file
if not exist credentials.txt (
    echo ERROR: credentials.txt not found!
    echo.
    echo Please make sure credentials.txt exists in the project root.
    pause
    exit /b 1
)

for /f "tokens=1,2 delims==" %%a in (credentials.txt) do (
    set %%a=%%b
)

echo Checking prerequisites...
echo.

REM Check AWS CLI
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not installed!
    echo.
    echo Please install from: https://awscli.amazonaws.com/AWSCLIV2.msi
    echo After installing, run this script again.
    pause
    exit /b 1
)
echo [OK] AWS CLI found

REM Check Docker
docker ps >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker is not running!
    echo.
    echo Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)
echo [OK] Docker is running

echo.
echo ========================================
echo Configuring AWS Credentials...
echo ========================================
echo.

aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region %AWS_DEFAULT_REGION%
aws configure set default.output json

REM Test credentials
aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS credentials are invalid!
    pause
    exit /b 1
)

echo [OK] AWS credentials configured
echo.

REM Get Account ID
for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo AWS Account ID: %ACCOUNT_ID%
echo.

echo ========================================
echo STEP 1: Creating AWS Infrastructure
echo ========================================
echo This will take 10-15 minutes...
echo.

REM Create CloudFormation stack
aws cloudformation create-stack ^
    --stack-name vibeagent-infrastructure ^
    --template-body file://aws/cloudformation-template.yml ^
    --capabilities CAPABILITY_IAM ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% EQU 0 (
    echo CloudFormation stack creation started...
    echo Waiting for stack to complete...
    echo.
    aws cloudformation wait stack-create-complete ^
        --stack-name vibeagent-infrastructure ^
        --region %AWS_DEFAULT_REGION%

    if %ERRORLEVEL% EQU 0 (
        echo [OK] Infrastructure created successfully!
    ) else (
        echo ERROR: Stack creation failed!
        echo Checking if stack already exists...
        aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --region %AWS_DEFAULT_REGION% >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo [OK] Stack already exists, continuing...
        ) else (
            echo Please check AWS Console for errors
            pause
            exit /b 1
        )
    )
) else (
    echo Stack might already exist, checking...
    aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --region %AWS_DEFAULT_REGION% >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Stack already exists, continuing...
    ) else (
        echo ERROR: Failed to create stack
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo STEP 2: Getting Infrastructure Details
echo ========================================
echo.

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set DB_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set REDIS_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set ALB_DNS=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`VPCId`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set VPC_ID=%%i

echo Database Endpoint: %DB_ENDPOINT%
echo Redis Endpoint: %REDIS_ENDPOINT%
echo Load Balancer DNS: %ALB_DNS%
echo VPC ID: %VPC_ID%
echo.

echo ========================================
echo STEP 3: Creating ECR Repository
echo ========================================
echo.

aws ecr create-repository ^
    --repository-name vibeagent-backend ^
    --region %AWS_DEFAULT_REGION% 2>nul

set ECR_URI=%ACCOUNT_ID%.dkr.ecr.%AWS_DEFAULT_REGION%.amazonaws.com/vibeagent-backend
echo [OK] ECR Repository: %ECR_URI%
echo.

echo ========================================
echo STEP 4: Building Docker Image
echo ========================================
echo.

cd backend
docker build -t vibeagent-backend:latest .
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker build failed!
    cd ..
    pause
    exit /b 1
)
cd ..

echo [OK] Docker image built successfully!
echo.

echo ========================================
echo STEP 5: Pushing to ECR
echo ========================================
echo.

REM Login to ECR
aws ecr get-login-password --region %AWS_DEFAULT_REGION% | docker login --username AWS --password-stdin %ECR_URI%

docker tag vibeagent-backend:latest %ECR_URI%:latest
docker push %ECR_URI%:latest

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Docker push failed!
    pause
    exit /b 1
)

echo [OK] Image pushed to ECR successfully!
echo.

echo ========================================
echo STEP 6: Creating Secrets
echo ========================================
echo.

REM Get database password
for /f "tokens=*" %%i in ('aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region %AWS_DEFAULT_REGION% 2^>nul') do set DB_SECRET=%%i

REM Parse JSON to get password (simplified)
echo %DB_SECRET% > temp_secret.json
for /f "tokens=2 delims=:}" %%a in ('findstr "password" temp_secret.json') do set DB_PASSWORD=%%a
set DB_PASSWORD=%DB_PASSWORD:"=%
set DB_PASSWORD=%DB_PASSWORD: =%
del temp_secret.json

echo Creating/updating secrets...

REM DATABASE_URL
aws secretsmanager create-secret ^
    --name vibeagent/database-url ^
    --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% NEQ 0 (
    aws secretsmanager update-secret ^
        --secret-id vibeagent/database-url ^
        --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" ^
        --region %AWS_DEFAULT_REGION%
)

REM REDIS_URL
aws secretsmanager create-secret ^
    --name vibeagent/redis-url ^
    --secret-string "redis://%REDIS_ENDPOINT%:6379/0" ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% NEQ 0 (
    aws secretsmanager update-secret ^
        --secret-id vibeagent/redis-url ^
        --secret-string "redis://%REDIS_ENDPOINT%:6379/0" ^
        --region %AWS_DEFAULT_REGION%
)

REM SECRET_KEY
aws secretsmanager create-secret ^
    --name vibeagent/secret-key ^
    --secret-string "vibeagent-super-secret-key-production-2024" ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% NEQ 0 (
    aws secretsmanager update-secret ^
        --secret-id vibeagent/secret-key ^
        --secret-string "vibeagent-super-secret-key-production-2024" ^
        --region %AWS_DEFAULT_REGION%
)

REM OPENROUTER_API_KEY
aws secretsmanager create-secret ^
    --name vibeagent/openrouter-key ^
    --secret-string "%OPENROUTER_API_KEY%" ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% NEQ 0 (
    aws secretsmanager update-secret ^
        --secret-id vibeagent/openrouter-key ^
        --secret-string "%OPENROUTER_API_KEY%" ^
        --region %AWS_DEFAULT_REGION%
)

echo [OK] All secrets created/updated
echo.

echo ========================================
echo STEP 7: Registering ECS Task Definition
echo ========================================
echo.

REM Update task definition with actual values
powershell -Command "(Get-Content aws/ecs-task-definition.json) -replace 'YOUR_ACCOUNT_ID', '%ACCOUNT_ID%' -replace 'YOUR_ECR_REGISTRY', '%ACCOUNT_ID%.dkr.ecr.%AWS_DEFAULT_REGION%.amazonaws.com' | Set-Content temp-task-def.json"

aws ecs register-task-definition ^
    --cli-input-json file://temp-task-def.json ^
    --region %AWS_DEFAULT_REGION%

del temp-task-def.json

echo [OK] Task definition registered
echo.

echo ========================================
echo STEP 8: Creating ECS Service
echo ========================================
echo.

REM Get subnet IDs
for /f %%i in ('aws ec2 describe-subnets --filters "Name=vpc-id,Values=%VPC_ID%" "Name=tag:Name,Values=*Public-Subnet-1" --query "Subnets[0].SubnetId" --output text --region %AWS_DEFAULT_REGION%') do set SUBNET_1=%%i
for /f %%i in ('aws ec2 describe-subnets --filters "Name=vpc-id,Values=%VPC_ID%" "Name=tag:Name,Values=*Public-Subnet-2" --query "Subnets[0].SubnetId" --output text --region %AWS_DEFAULT_REGION%') do set SUBNET_2=%%i

REM Get security group
for /f %%i in ('aws ec2 describe-security-groups --filters "Name=vpc-id,Values=%VPC_ID%" "Name=group-name,Values=*ECSSecurityGroup*" --query "SecurityGroups[0].GroupId" --output text --region %AWS_DEFAULT_REGION%') do set SECURITY_GROUP=%%i

REM Get target group ARN
for /f %%i in ('aws elbv2 describe-target-groups --names production-tg --query "TargetGroups[0].TargetGroupArn" --output text --region %AWS_DEFAULT_REGION%') do set TARGET_GROUP_ARN=%%i

echo Subnets: %SUBNET_1%, %SUBNET_2%
echo Security Group: %SECURITY_GROUP%
echo Target Group: %TARGET_GROUP_ARN%
echo.

REM Create ECS service
aws ecs create-service ^
    --cluster vibeagent-cluster ^
    --service-name vibeagent-backend-service ^
    --task-definition vibeagent-backend ^
    --desired-count 1 ^
    --launch-type FARGATE ^
    --network-configuration "awsvpcConfiguration={subnets=[%SUBNET_1%,%SUBNET_2%],securityGroups=[%SECURITY_GROUP%],assignPublicIp=ENABLED}" ^
    --load-balancers "targetGroupArn=%TARGET_GROUP_ARN%,containerName=vibeagent-backend,containerPort=8000" ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% NEQ 0 (
    echo Service might already exist, updating...
    aws ecs update-service ^
        --cluster vibeagent-cluster ^
        --service vibeagent-backend-service ^
        --force-new-deployment ^
        --region %AWS_DEFAULT_REGION%
)

echo [OK] ECS service created/updated
echo.

echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Your Backend API is deploying...
echo.
echo Backend API URL: http://%ALB_DNS%
echo API Documentation: http://%ALB_DNS%/docs
echo Health Check: http://%ALB_DNS%/health
echo.
echo IMPORTANT: Save this URL for Vercel deployment!
echo.
echo Next Steps:
echo 1. Wait 3-5 minutes for ECS service to start
echo 2. Test: Open http://%ALB_DNS%/health in browser
echo 3. You should see: {"status":"healthy"}
echo.
echo Then follow the Vercel deployment steps!
echo.

REM Save URL to file
echo %ALB_DNS% > BACKEND_URL.txt
echo Backend URL saved to BACKEND_URL.txt
echo.

pause
