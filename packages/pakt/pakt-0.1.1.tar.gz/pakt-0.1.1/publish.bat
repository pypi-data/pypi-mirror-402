@echo off
setlocal

echo Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo Building package...
python -m build
if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Uploading to PyPI...
twine upload dist/*
if errorlevel 1 (
    echo Upload failed!
    pause
    exit /b 1
)

echo.
echo Done! Check https://pypi.org/project/pakt/
pause
