@echo off
REM Finish creating AWS Secrets

echo Loading credentials...
for /f "tokens=1,2 delims==" %%a in (credentials.txt) do (
    set %%a=%%b
)

aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region us-east-1

echo.
echo Getting infrastructure details...

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue" --output text --region us-east-1') do set DB_ENDPOINT=%%i

for /f %%i in ('aws cloudformation describe-stacks --stack-name vibeagent-infrastructure --query "Stacks[0].Outputs[?OutputKey==`RedisEndpoint`].OutputValue" --output text --region us-east-1') do set REDIS_ENDPOINT=%%i

echo Database: %DB_ENDPOINT%
echo Redis: %REDIS_ENDPOINT%
echo.

echo Getting database password using PowerShell...
powershell -Command "$secret = aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region us-east-1 | ConvertFrom-Json; $password = $secret.password; aws secretsmanager create-secret --name vibeagent/database-url --secret-string \"postgresql+asyncpg://postgres:$password@%DB_ENDPOINT%:5432/vibeagent\" --region us-east-1 2>$null; if ($LASTEXITCODE -ne 0) { aws secretsmanager update-secret --secret-id vibeagent/database-url --secret-string \"postgresql+asyncpg://postgres:$password@%DB_ENDPOINT%:5432/vibeagent\" --region us-east-1 }"

aws secretsmanager create-secret --name vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/redis-url --secret-string "redis://%REDIS_ENDPOINT%:6379/0" --region us-east-1

aws secretsmanager create-secret --name vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/secret-key --secret-string "vibeagent-super-secret-key-production-2024" --region us-east-1

aws secretsmanager create-secret --name vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1 2>nul || aws secretsmanager update-secret --secret-id vibeagent/openrouter-key --secret-string "%OPENROUTER_API_KEY%" --region us-east-1

echo.
echo [OK] All secrets created!
echo.

echo Registering ECS task definition...

for /f %%i in ('aws sts get-caller-identity --query Account --output text') do set ACCOUNT_ID=%%i

powershell -Command "(Get-Content aws/ecs-task-definition.json) -replace 'YOUR_ACCOUNT_ID', '%ACCOUNT_ID%' -replace 'YOUR_ECR_REGISTRY', '%ACCOUNT_ID%.dkr.ecr.us-east-1.amazonaws.com' | Set-Content temp-task-def.json"

aws ecs register-task-definition --cli-input-json file://temp-task-def.json --region us-east-1
del temp-task-def.json

echo.
echo ========================================
echo DEPLOYMENT COMPLETE!
echo ========================================
echo.
echo Backend URL: http://production-alb-1567753423.us-east-1.elb.amazonaws.com
echo Database: %DB_ENDPOINT%
echo Redis: %REDIS_ENDPOINT%
echo.
echo NEXT STEP: Re-run GitHub Actions workflow
echo   https://github.com/preetugc1234/AI-agent-builder/actions
echo.
echo Click "Re-run all jobs" on the failed workflow
echo It will deploy your backend to ECS!
echo.

pause
