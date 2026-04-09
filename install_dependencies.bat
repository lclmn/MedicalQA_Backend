@echo off
echo Installing backend dependencies for BERT-based Q&A system...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python first
    pause
    exit /b 1
)

REM Install required packages
echo Installing required Python packages...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.
echo Next steps:
echo 1. Make sure Neo4j is running on localhost:7687
echo 2. Make sure MySQL is running on localhost:3306
echo 3. Import English data: python import_english_data.py
echo 4. Run run_backend.bat to start the backend server
echo.
pause 