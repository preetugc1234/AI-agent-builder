@echo off
REM Deploy FULL Infrastructure with RDS + Redis (FIXED VERSION)

echo ========================================
echo FULL INFRASTRUCTURE DEPLOYMENT
echo ========================================
echo.
echo This creates:
echo - VPC and Subnets
echo - RDS PostgreSQL Database (Fixed version!)
echo - ElastiCache Redis
echo - ECS Cluster
echo - Application Load Balancer
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
echo Step 1: Deleting old failed stack...
aws cloudformation delete-stack --stack-name vibeagent-infrastructure --region us-east-1 2>nul

echo Waiting for deletion (2-3 minutes)...
timeout /t 120 /nobreak >nul

echo.
echo Step 2: Creating FULL infrastructure with FIXED template...
aws cloudformation create-stack ^
    --stack-name vibeagent-infrastructure ^
    --template-body file://aws/cloudformation-template.yml ^
    --capabilities CAPABILITY_IAM ^
    --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create stack!
    pause
    exit /b 1
)

echo.
echo Stack creation started!
echo.
echo This will take 10-15 minutes - creating:
echo - VPC, Subnets, Security Groups (2-3 min)
echo - RDS PostgreSQL (5-7 min)
echo - ElastiCache Redis (3-5 min)
echo - Load Balancer (2-3 min)
echo - ECS Cluster (1 min)
echo.
echo Please wait...
echo.

aws cloudformation wait stack-create-complete --stack-name vibeagent-infrastructure --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Stack creation failed!
    echo.
    echo Checking what failed...
    aws cloudformation describe-stack-events --stack-name vibeagent-infrastructure --region us-east-1 --output json > stack-events-error.json
    echo.
    echo Error details saved to: stack-events-error.json
    echo Open it and search for "CREATE_FAILED" to see the error
    pause
    exit /b 1
)

echo.
echo [OK] Stack created successfully!
echo.

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

echo.
echo Creating AWS Secrets...

REM Get database password
for /f "tokens=*" %%i in ('aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region us-east-1 2^>nul') do set DB_SECRET=%%i

if "%DB_SECRET%"=="" (
    echo Warning: Could not get database password
    set DB_PASSWORD=change-me-later
) else (
    echo %DB_SECRET% > temp_secret.json
    for /f "tokens=2 delims=:}" %%a in ('findstr "password" temp_secret.json') do set DB_PASSWORD=%%a
    set DB_PASSWORD=%DB_PASSWORD:"=%
    set DB_PASSWORD=%DB_PASSWORD: =%
    del temp_secret.json
)

echo Creating/updating secrets...

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
echo FULL INFRASTRUCTURE READY!
echo ========================================
echo.
echo Backend URL: http://%ALB_DNS%
echo Database: %DB_ENDPOINT%
echo Redis: %REDIS_ENDPOINT%
echo.
echo NEXT: Re-run GitHub Actions workflow
echo   https://github.com/preetugc1234/AI-agent-builder/actions
echo.
echo Click "Re-run all jobs" on the failed workflow
echo It will deploy your backend with RDS + Redis!
echo.

pause
