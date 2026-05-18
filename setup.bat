@echo off
echo ========================================
echo  Strulovitz Ghost - One-Click Setup
echo ========================================
echo.

echo [1/4] Creating conda environment...
call conda create -n strulovitzghost python=3.12 -y
if %errorlevel% neq 0 (
    echo ERROR: Failed to create conda environment.
    pause
    exit /b 1
)

echo [2/4] Installing Python packages...
call conda run -n strulovitzghost pip install flask flask-sqlalchemy pyqt6 pillow requests python-dotenv
call conda run -n strulovitzghost pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
call conda run -n strulovitzghost pip install diffusers transformers accelerate sentencepiece bitsandbytes

echo [3/4] Installing ComfyUI...
if not exist "src\comfyui" (
    echo Cloning ComfyUI...
    git clone https://github.com/comfyanonymous/ComfyUI.git src\comfyui --depth 1
)
call conda run -n strulovitzghost pip install -r src\comfyui\requirements.txt

echo [4/4] Setup complete!
echo.
echo Models are NOT downloaded yet (saves disk space).
echo After starting the GUI, use the "Download Models" buttons
echo in the Worker tab to download the AI models you need.
echo.
echo To start the server: run_server.bat
echo To start the GUI:    run_gui.bat
echo.
pause
