@echo off
setlocal

echo.
echo [1/6] Upgrade pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail

echo.
echo [2/6] Remove old torch packages...
python -m pip uninstall -y torch torchvision torchaudio

echo.
echo [3/6] Install CPU-only PyTorch 2.3.1...
python -m pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 goto :fail

echo.
echo [4/6] Install sentence-transformers...
python -m pip install sentence-transformers==3.0.1
if errorlevel 1 goto :fail

echo.
echo [5/6] Install Neo4j driver...
python -m pip install neo4j==5.20.0
if errorlevel 1 goto :fail

echo.
echo [6/6] Install other required packages...
python -m pip install google-generativeai pdfplumber numpy scikit-learn
if errorlevel 1 goto :fail

echo.
echo Installation complete.
echo Verify with:
echo python -c "import torch; print('torch OK:', torch.__version__)"
echo.
pause
exit /b 0

:fail
echo.
echo Installation failed. Check the error messages above.
pause
exit /b 1
