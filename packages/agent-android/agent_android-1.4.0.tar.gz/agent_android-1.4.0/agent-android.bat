@echo off
REM agent-android CLI wrapper for Windows

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    exit /b 1
)

REM Get script directory
set SCRIPT_DIR=%~dp0

REM Run agent-android with Python
python "%SCRIPT_DIR%agent-android" %*
