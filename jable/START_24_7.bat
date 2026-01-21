@echo off
echo ========================================
echo   24/7 AUTOMATIC PIPELINE
echo ========================================
echo.
echo This will run continuously until stopped.
echo Press Ctrl+C to stop.
echo.
pause

cd /d "%~dp0"
python run_24_7.py

pause
