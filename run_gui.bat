@echo off
echo Starting Strulovitz Ghost GUI...
call conda activate strulovitzghost
cd /d "%~dp0src"
python gui.py
pause
