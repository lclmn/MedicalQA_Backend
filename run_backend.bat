@echo off
echo Starting Medical Q&A Backend Server (BERT-based)...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)
set HF_ENDPOINT=https://hf-mirror.com
set HF_HUB_OFFLINE=0
REM Start the Flask application
echo Backend server starting on http://127.0.0.1:5001
echo Press Ctrl+C to stop the server
echo.
python app.py

pause 