@echo off
echo ========================================================
echo   SENTRA -- Local-First Scene Observation Setup (Windows)
echo ========================================================

python -m venv .venv
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

echo Activating virtual environment...
call .\.venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================================
echo   SENTRA Setup Complete! Run 'run.bat' to launch.
echo ========================================================
pause
