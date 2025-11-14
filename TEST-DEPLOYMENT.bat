@echo off
REM Test if deployment is working

echo ========================================
echo Testing Backend Deployment
echo ========================================
echo.

if not exist BACKEND_URL.txt (
    echo ERROR: Backend URL not found!
    echo Please run DEPLOY-NOW.bat first
    pause
    exit /b 1
)

set /p BACKEND_URL=<BACKEND_URL.txt

echo Backend URL: http://%BACKEND_URL%
echo.
echo Testing health endpoint...
echo.

curl http://%BACKEND_URL%/health

echo.
echo.
echo If you see {"status":"healthy"} above, deployment is successful!
echo.
pause
