@echo off
REM Fix Database URL - URL encode special characters in password

echo Loading credentials...
for /f "tokens=1,2 delims==" %%a in (credentials.txt) do (
    set %%a=%%b
)

aws configure set aws_access_key_id %AWS_ACCESS_KEY_ID%
aws configure set aws_secret_access_key %AWS_SECRET_ACCESS_KEY%
aws configure set default.region us-east-1

echo Getting database password and encoding it...

powershell -Command "$secret = aws secretsmanager get-secret-value --secret-id vibeagent/database-password --query SecretString --output text --region us-east-1 | ConvertFrom-Json; $password = $secret.password; Add-Type -AssemblyName System.Web; $encodedPassword = [System.Web.HttpUtility]::UrlEncode($password); $dbUrl = \"postgresql+asyncpg://postgres:$encodedPassword@vibeagent-db.ccb0ow6mqymf.us-east-1.rds.amazonaws.com:5432/vibeagent\"; Write-Host \"New DB URL: $dbUrl\"; aws secretsmanager update-secret --secret-id vibeagent/database-url --secret-string $dbUrl --region us-east-1"

echo.
echo [OK] Database URL fixed with URL-encoded password!
echo.
echo Now restart the ECS service...

aws ecs update-service --cluster production-cluster --service vibeagent-backend-service --force-new-deployment --region us-east-1

echo.
echo [OK] Service restarting with fixed database URL!
echo.

pause
