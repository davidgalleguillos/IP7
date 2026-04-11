@echo off
set PYTHONPATH=%PYTHONPATH%;%CD%
.\venv\Scripts\python.exe %CD%\ipv7\cli.py %*
