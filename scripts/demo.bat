@echo off
rem Double-click launcher for the demo tunnel.
rem
rem Keep THIS file ASCII-only. cmd.exe reads .bat files in the system codepage
rem (cp949 here), so UTF-8 Korean text breaks line parsing and the script dies
rem with "not recognized as an internal or external command" errors.
rem All Korean output lives in demo.ps1, which PowerShell reads as UTF-8.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0demo.ps1"
if errorlevel 1 pause
