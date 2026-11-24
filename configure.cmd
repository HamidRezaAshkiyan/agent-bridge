@echo off
rem Agent Bridge - AI provider configurator (cmd.exe shim).
rem Delegates to configure.ps1 so there is a single source of truth.
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0configure.ps1" %*
exit /b %ERRORLEVEL%
