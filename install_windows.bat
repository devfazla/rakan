@echo off
REM RAKAN Installation Script for Windows
REM This script adds RAKAN to your system PATH

echo ====================================
echo RAKAN Installation Script
echo ====================================
echo.

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "RAKAN_DIR=%SCRIPT_DIR%"

echo RAKAN Directory: %RAKAN_DIR%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version
echo.

REM Check if rakan is already in PATH
where rakan >nul 2>&1
if %errorlevel% equ 0 (
    echo RAKAN is already in PATH
    where rakan
    echo.
    set /p choice="Do you want to reinstall RAKAN? (y/n): "
    if /i not "%choice%"=="y" (
        echo Installation cancelled
        pause
        exit /b 0
    )
)

REM Create the batch file wrapper
set "WRAPPER_FILE=%USERPROFILE%\rakan.bat"
echo Creating RAKAN wrapper at: %WRAPPER_FILE%

(
    echo @echo off
    echo python "%RAKAN_DIR%cli\main.py" %%*
) > "%WRAPPER_FILE%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create wrapper file
    pause
    exit /b 1
)

echo Wrapper file created successfully
echo.

REM Add to PATH (current user)
echo Adding RAKAN to user PATH...
for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%B"

if defined USER_PATH (
    echo %USER_PATH% | find /i "%USERPROFILE%" >nul
    if %errorlevel% neq 0 (
        set "NEW_PATH=%USER_PATH%;%USERPROFILE%"
    ) else (
        set "NEW_PATH=%USER_PATH%"
    )
) else (
    set "NEW_PATH=%USERPROFILE%"
)

setx PATH "%NEW_PATH%" >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Failed to update PATH automatically
    echo Please add %USERPROFILE% to your PATH manually
    echo.
    echo Manual steps:
    echo 1. Press Win+R, type "sysdm.cpl" and press Enter
    echo 2. Go to Advanced tab, click Environment Variables
    echo 3. Under User variables, find PATH and click Edit
    echo 4. Add %USERPROFILE% to the list
    echo 5. Close and reopen your terminal
) else (
    echo PATH updated successfully
    echo.
    echo IMPORTANT: Close and reopen your terminal for changes to take effect
)

echo.
echo ====================================
echo Installation Complete!
echo ====================================
echo.
echo To use RAKAN:
echo 1. Close and reopen your terminal
echo 2. Run: rakan --help
echo.
echo Wrapper file location: %WRAPPER_FILE%
echo.

pause