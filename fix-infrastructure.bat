@echo off
REM Fix AWS Infrastructure Issues

echo ========================================
echo FIXING AWS INFRASTRUCTURE
echo ========================================
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

echo Configuring AWS...
aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region us-east-1

echo.
echo Checking stack status...
aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --region us-east-1 2>temp_error.txt

if %ERRORLEVEL% NEQ 0 (
    echo Stack doesn't exist. Creating new...
    goto CREATE_STACK
)

REM Get stack status
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].StackStatus" --output text --region us-east-1 2^>nul') do set STACK_STATUS=%%i

echo Current stack status: %STACK_STATUS%
echo.

if "%STACK_STATUS%"=="CREATE_COMPLETE" (
    echo Stack already exists and is healthy!
    echo Getting infrastructure details...
    goto GET_DETAILS
)

if "%STACK_STATUS%"=="UPDATE_COMPLETE" (
    echo Stack already exists and is healthy!
    echo Getting infrastructure details...
    goto GET_DETAILS
)

echo Stack is in bad state: %STACK_STATUS%
echo Deleting and recreating...
echo.

:DELETE_STACK
echo Deleting old stack...
aws cloudformation delete-stack --stack-name vibeagent-infrastructure --region us-east-1

echo Waiting for deletion (this may take 5-10 minutes)...
aws cloudformation wait stack-delete-complete --stack-name vibeagent-infrastructure --region us-east-1

echo Stack deleted successfully!
echo.

:CREATE_STACK
echo Creating new stack...
aws cloudformation create-stack ^
    --stack-name vibeagent-infrastructure ^
    --template-body file://aws/cloudformation-template.yml ^
    --capabilities CAPABILITY_IAM ^
    --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create stack!
    type temp_error.txt 2>nul
    del temp_error.txt 2>nul
    pause
    exit /b 1
)

echo.
echo Stack creation started!
echo Waiting for completion (10-15 minutes)...
echo Please be patient...
echo.

aws cloudformation wait stack-create-complete --stack-name vibeagent-infrastructure --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Stack creation failed!
    echo Checking error...
    aws cloudformation describe-stack-events --stack-name vibeagent-infrastructure --region us-east-1 --max-items 5
    pause
    exit /b 1
)

echo.
echo [OK] Stack created successfully!
echo.

:GET_DETAILS
echo Getting infrastructure details...

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue" --output text --region us-east-1') do set DB_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue" --output text --region us-east-1') do set REDIS_ENDPOINT=%%i
for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue" --output text --region us-east-1') do set ALB_DNS=%%i

echo.
echo Database: %DB_ENDPOINT%
echo Redis: %REDIS_ENDPOINT%
echo Load Balancer: %ALB_DNS%
echo.

echo Saving backend URL...
echo %ALB_DNS% > BACKEND_URL.txt

echo Creating AWS Secrets...

REM Get database password
for /f "tokens=*" %%i in ('aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region us-east-1 2^>nul') do set DB_SECRET=%%i

if "%DB_SECRET%"=="" (
    echo Error: Could not get database password
    pause
    exit /b 1
)

REM Extract password from JSON
echo %DB_SECRET% > temp_secret.json
for /f "tokens=2 delims=:}" %%a in ('findstr "password" temp_secret.json') do set DB_PASSWORD=%%a
set DB_PASSWORD=%DB_PASSWORD:"=%
set DB_PASSWORD=%DB_PASSWORD: =%
del temp_secret.json

echo Creating secrets...

aws secretsmanager create-secret --name vibeagent/database-url --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/database-url --secret-string "postgresql+asyncpg://postgres:%DB_PASSWORD%@%DB_ENDPOINT%:5432/vibeagent" --region us-east-1

aws secretsmanager create-secret --name vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region us-east-1

aws secretsmanager create-secret --name vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1

aws secretsmanager create-secret --name vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1

echo [OK] Secrets created!
echo.

echo Registering ECS task definition...

for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

powershell -Command "(Get-Content aws/ecs-task-definition.json) -replace 'YOUR_ACCOUNT_ID', '%ACCOUNT_ID%' -replace 'YOUR_ECR_REGISTRY', '%ACCOUNT_ID%.dkr.ecr.us-east-1.amazonaws.com' | Set-Content temp-task-def.json"

aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region us-east-1 2>nul
del temp-task-def.json

echo [OK] Task definition registered!
echo.

echo ========================================
echo INFRASTRUCTURE READY!
echo ========================================
echo.
echo Backend URL: http://%ALB_DNS%
echo.
echo NEXT: Push code to GitHub to deploy!
echo   git push origin main
echo.
echo Or re-run failed workflow:
echo   https://github.com/preetugc1234/AI-agent-builder/actions
echo.

del temp_error.txt 2>nul

pause
