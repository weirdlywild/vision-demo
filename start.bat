@echo off
echo ========================================
echo DIY Repair Diagnosis API
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file with your OpenAI API key:
    echo   1. Copy .env.example to .env
    echo   2. Edit .env and add your OpenAI API key
    echo.
    pause
    exit /b 1
)

echo Starting server...
echo.
echo Web Interface: http://localhost:8000
echo API Docs:      http://localhost:8000/docs
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
