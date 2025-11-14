@echo off
REM Quick Deploy - Minimal Infrastructure (No RDS/Redis)

echo ========================================
echo QUICK DEPLOY - MINIMAL INFRASTRUCTURE
echo ========================================
echo.
echo This creates ONLY:
echo - VPC and Subnets
echo - ECS Cluster
echo - Application Load Balancer
echo.
echo NO RDS or Redis (we'll add later if needed)
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
echo Deleting old stack if exists...
aws cloudformation delete-stack --stack-name vibeagent-infrastructure --region us-east-1 2>nul
timeout /t 60 /nobreak >nul

echo.
echo Creating MINIMAL infrastructure...
aws cloudformation create-stack ^
    --stack-name vibeagent-infrastructure ^
    --template-body file://aws/simple-infrastructure.yml ^
    --capabilities CAPABILITY_IAM ^
    --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create stack!
    pause
    exit /b 1
)

echo.
echo Stack creation started!
echo Waiting for completion (5-7 minutes - much faster!)...
echo.

aws cloudformation wait stack-create-complete --stack-name vibeagent-infrastructure --region us-east-1

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Stack creation failed!
    pause
    exit /b 1
)

echo.
echo [OK] Stack created successfully!
echo.

echo Getting infrastructure details...

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue" --output text --region us-east-1') do set ALB_DNS=%%i

echo.
echo Load Balancer: %ALB_DNS%
echo.

echo Saving backend URL...
echo %ALB_DNS% > BACKEND_URL.txt

echo Creating basic secrets...

aws secretsmanager create-secret --name vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1

aws secretsmanager create-secret --name vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1

echo [OK] Secrets created!
echo.

echo Registering ECS task definition...

for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

powershell -Command "(Get-Content aws/ecs-task-definition.json) -replace 'YOUR_ACCOUNT_ID', '%ACCOUNT_ID%' -replace 'YOUR_ECR_REGISTRY', '%ACCOUNT_ID%.dkr.ecr.us-east-1.amazonaws.com' | Set-Content temp-task-def.json"

aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region us-east-1 2>nul
del temp-task-def.json

echo [OK] Done!
echo.

echo ========================================
echo INFRASTRUCTURE READY!
echo ========================================
echo.
echo Backend URL: http://%ALB_DNS%
echo.
echo NEXT: Re-run GitHub Actions workflow
echo   https://github.com/preetugc1234/AI-agent-builder/actions
echo.
echo Click "Re-run all jobs" on the failed workflow
echo.

pause
