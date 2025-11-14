@echo off
REM Setup AWS Infrastructure (CloudFormation only - No Docker needed!)

echo ========================================
echo VIBEAGENT FORGE - INFRASTRUCTURE SETUP
echo ========================================
echo.
echo This script creates the AWS infrastructure.
echo Docker builds will happen on GitHub Actions automatically!
echo.

REM Load credentials
if not exist credentials.txt (
    echo ERROR: credentials.txt not found!
    echo.
    echo Please make sure credentials.txt exists with:
    echo AWS_ACCESS_KEY_ID=your-key
    echo AWS_SECRET_ACCESS_KEY=your-secret
    echo AWS_DEFAULT_REGION=us-east-1
    echo OPENROUTER_API_KEY=your-openrouter-key
    pause
    exit /b 1
)

for /f "tokens=1,2 delims==" %%a in (credentials.txt) do (
    set %%a=%%b
)

echo Checking AWS CLI...
where aws >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: AWS CLI not installed!
    echo Download from: https://awscli.amazonaws.com/AWSCLIV2.msi
    pause
    exit /b 1
)
echo [OK] AWS CLI found
echo.

echo Configuring AWS credentials...
aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region %AWS_DEFAULT_REGION%
aws configure set default.output json

aws sts get-caller-identity >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Invalid AWS credentials!
    pause
    exit /b 1
)
echo [OK] AWS credentials valid
echo.

for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i
echo AWS Account ID: %ACCOUNT_ID%
echo.

echo ========================================
echo Creating AWS Infrastructure...
echo ========================================
echo This takes 10-15 minutes...
echo.

aws cloudformation create-stack ^
    --stack-name vibeagent-infrastructure ^
    --template-body file://aws/cloudformation-template.yml ^
    --capabilities CAPABILITY_IAM ^
    --region %AWS_DEFAULT_REGION% 2>nul

if %ERRORLEVEL% EQU 0 (
    echo Stack creation started...
    echo Waiting for completion...
    aws cloudformation wait stack-create-complete ^
        --stack-name vibeagent-infrastructure ^
        --region %AWS_DEFAULT_REGION%

    if %ERRORLEVEL% EQU 0 (
        echo [OK] Infrastructure created!
    ) else (
        echo Warning: Stack creation timeout or already exists
        aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --region %AWS_DEFAULT_REGION% >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo [OK] Stack exists, continuing...
        )
    )
) else (
    echo Stack already exists, checking...
    aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --region %AWS_DEFAULT_REGION% >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Stack exists, continuing...
    ) else (
        echo ERROR: Failed to create/find stack
        pause
        exit /b 1
    )
)

echo.
echo Getting infrastructure details...

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set DB_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set REDIS_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue" --output text --region %AWS_DEFAULT_REGION%') do set ALB_DNS=%%i

echo.
echo Database: %DB_ENDPOINT%
echo Redis: %REDIS_ENDPOINT%
echo Load Balancer: %ALB_DNS%
echo.

echo Creating AWS Secrets...

REM Get database password
for /f "tokens=*" %%i in ('aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region %AWS_DEFAULT_REGION% 2^>nul') do set DB_SECRET=%%i

REM Simple password extraction
echo %DB_SECRET% > temp_secret.json
for /f "tokens=2 delims=:}" %%a in ('findstr "password" temp_secret.json') do set DB_PASSWORD=%%a
set DB_PASSWORD=%DB_PASSWORD:"=%
set DB_PASSWORD=%DB_PASSWORD: =%
del temp_secret.json

echo Creating secrets...

aws secretsmanager create-secret --name vibeagent/database-url --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" --region %AWS_DEFAULT_REGION% 2>nul || aws secretsmanager update-secret --secret-id vibeagent/database-url --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" --region %AWS_DEFAULT_REGION%

aws secretsmanager create-secret --name vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region %AWS_DEFAULT_REGION% 2>nul || aws secretsmanager update-secret --secret-id vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region %AWS_DEFAULT_REGION%

aws secretsmanager create-secret --name vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region %AWS_DEFAULT_REGION% 2>nul || aws secretsmanager update-secret --secret-id vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region %AWS_DEFAULT_REGION%

aws secretsmanager create-secret --name vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region %AWS_DEFAULT_REGION% 2>nul || aws secretsmanager update-secret --secret-id vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region %AWS_DEFAULT_REGION%

echo [OK] Secrets created
echo.

REM Create initial ECS task definition (will be updated by GitHub Actions)
echo Registering initial ECS task definition...

powershell -Command "(Get-Content aws/ecs-task-definition.json) -replace 'YOUR_ACCOUNT_ID', '%ACCOUNT_ID%' -replace 'YOUR_ECR_REGISTRY', '%ACCOUNT_ID%.dkr.ecr.%AWS_DEFAULT_REGION%.amazonaws.com' | Set-Content temp-task-def.json"

aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region %AWS_DEFAULT_REGION% 2>nul
del temp-task-def.json

echo.
echo ========================================
echo INFRASTRUCTURE SETUP COMPLETE!
echo ========================================
echo.
echo Backend URL: http://%ALB_DNS%
echo.
echo Saving URL...
echo %ALB_DNS% > BACKEND_URL.txt
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo.
echo 1. Add secrets to GitHub:
echo    - Go to: https://github.com/preetugc1234/AI-agent-builder/settings/secrets/actions
echo    - Click "New repository secret"
echo    - Add these secrets:
echo.
echo      Name: AWS_ACCESS_KEY_ID
echo      Value: %AWS_ACCESS_KEY_ID%
echo.
echo      Name: AWS_SECRET_ACCESS_KEY
echo      Value: %AWS_SECRET_ACCESS_KEY%
echo.
echo      Name: OPENROUTER_API_KEY
echo      Value: %OPENROUTER_API_KEY%
echo.
echo 2. Push code to GitHub:
echo    git add .
echo    git commit -m "Setup infrastructure"
echo    git push origin main
echo.
echo 3. GitHub Actions will automatically:
echo    - Build Docker image (in cloud)
echo    - Deploy to AWS ECS
echo    - No Docker Desktop needed!
echo.
echo 4. Check deployment status:
echo    https://github.com/preetugc1234/AI-agent-builder/actions
echo.

pause
