@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 --version >nul 2>&1
    if %errorlevel%==0 (
        py -3 "%SCRIPT_DIR%lib\install_agent.py" %*
        exit /b %errorlevel%
    )
)

where python >nul 2>&1
if %errorlevel%==0 (
    python --version >nul 2>&1
    if %errorlevel%==0 (
        python "%SCRIPT_DIR%lib\install_agent.py" %*
        exit /b %errorlevel%
    )
)

where python3 >nul 2>&1
if %errorlevel%==0 (
    python3 --version >nul 2>&1
    if %errorlevel%==0 (
        python3 "%SCRIPT_DIR%lib\install_agent.py" %*
        exit /b %errorlevel%
    )
)

echo Error: Python 3.8+ is required. Install it via: winget install Python.Python.3.12 >&2
exit /b 1
