@echo off
REM Council of Wise Men - PC launcher with auto-restart on crash
cd /d "%~dp0"
:loop
echo [%date% %time%] Starting bot...
python main.py
echo [%date% %time%] Bot exited with code %errorlevel%. Restarting in 10s... (Ctrl+C twice to stop)
timeout /t 10 /nobreak >nul
goto loop
