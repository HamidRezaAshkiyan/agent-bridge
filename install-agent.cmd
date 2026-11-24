@echo off
rem Agent Bridge - coding agent installer (cmd.exe shim).
rem Delegates to install-agent.ps1 so there is a single source of truth.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-agent.ps1" %*
exit /b %ERRORLEVEL%
