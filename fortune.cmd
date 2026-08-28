@echo off
rem fortune launcher (ASCII-safe; no pip install required)
chcp 65001 >nul
set "PYTHONIOENCODING=utf-8"
set "PYTHONPATH=%~dp0;%PYTHONPATH%"
"%~dp0.venv\Scripts\python.exe" -m fortune.cli %*
