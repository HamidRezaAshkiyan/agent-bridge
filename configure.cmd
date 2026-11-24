@echo off
rem Agent Bridge - AI provider configurator (cmd.exe shim).
rem
rem Runs the Python entry point directly so cmd users do not pay for a PowerShell
rem launch. Falls back to configure.ps1 (which also knows about the 'py -3'
rem launcher) when no Python is on PATH.
setlocal
set "SCRIPT_DIR=%~dp0"
set "AB_PY="

for %%P in (python.exe python3.exe) do (
    if not defined AB_PY (
        where %%P >nul 2>nul && set "AB_PY=%%P"
    )
)

if not defined AB_PY goto :use_powershell

"%AB_PY%" "%SCRIPT_DIR%lib\configure.py" %*
goto :done

:use_powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%configure.ps1" %*

:done
rem %ERRORLEVEL% must be read here, outside any parenthesised block, or it is
rem expanded when the block is parsed instead of after Python runs.
exit /b %ERRORLEVEL%
