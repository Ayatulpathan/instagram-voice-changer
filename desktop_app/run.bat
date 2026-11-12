@echo off
title Bangla AI Voice Real-Time Converter
cd /d "%~dp0"
echo ========================================================
echo   Bangla AI Voice Real-Time Converter (Colab GPU Bridge)
echo ========================================================
echo Starting desktop application...
"%~dp0.venv\Scripts\python.exe" "%~dp0gui_client.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application stopped or encountered an issue.
    pause
)
