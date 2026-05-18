@echo off
echo Starting Strulovitz Ghost Flask Server...
call conda activate strulovitzghost
cd /d "%~dp0src"
python app.py
pause
