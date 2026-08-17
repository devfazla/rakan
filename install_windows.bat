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

REM Check for force mode
set "FORCE_MODE=0"
if "%1"=="--force" set "FORCE_MODE=1"
if "%1"=="-f" set "FORCE_MODE=1"

if %FORCE_MODE%==1 (
    echo Force mode enabled - proceeding with reinstallation
)

REM Check for existing installation
if exist "%USERPROFILE%\.rakan\.installation_info" (
    if %FORCE_MODE%==0 (
        echo ====================================
        echo Existing Installation Detected
        echo ====================================
        echo.
        echo RAKAN appears to be already installed.
        echo.
        for /f "tokens=*" %%i in (%USERPROFILE%\.rakan\.installation_info) do set "EXISTING_INSTALL=%%i"
        echo Previous installation: %%i
        echo Current directory: %RAKAN_DIR%
        echo.
        
        REM Check if the installation directory exists
        if exist "%%i" (
            if "%RAKAN_DIR%"=="%%i" (
                echo This is the same installation directory.
                echo No installation needed.
                echo.
                echo To reinstall, first uninstall with:
                echo   rakan uninstall
                echo Or reinstall with force flag:
                echo   install_windows.bat --force
                pause
                exit /b 0
            ) else (
                echo Different installation directory detected.
                echo.
                echo Options:
                echo   1. Cancel and use existing installation
                echo   2. Reinstall this location
                echo   3. Uninstall existing and install new
                echo.
                set /p choice="Your choice (1/2/3): "
                
                if "%choice%"=="1" (
                    echo Installation cancelled.
                    echo Using existing installation at: %%i
                    pause
                    exit /b 0
                ) else if "%choice%"=="2" (
                    echo Proceeding with reinstallation...
                    echo This will overwrite the existing installation.
                ) else if "%choice%"=="3" (
                    echo Please uninstall existing installation first:
                    echo   rakan uninstall
                    echo Then run this installation again.
                    pause
                    exit /b 0
                ) else (
                    echo Invalid choice. Installation cancelled.
                    pause
                    exit /b 0
                )
            )
        ) else (
            echo Previous installation directory not found.
            echo This may be a corrupted installation.
            echo.
            echo Options:
            echo   1. Clean up and reinstall this location
            echo   2. Cancel and investigate
            echo.
            set /p choice="Your choice (1/2): "
            
            if "%choice%"=="1" (
                echo Cleaning up corrupted installation marker...
                del "%USERPROFILE%\.rakan\.installation_info"
                echo [OK] Removed corrupted marker
                echo Proceeding with installation...
            ) else if "%choice%"=="2" (
                echo Installation cancelled.
                echo Please check: %%i
                pause
                exit /b 0
            ) else (
                echo Invalid choice. Installation cancelled.
                pause
                exit /b 0
            )
        )
    ) else (
        echo Force mode enabled - skipping duplicate check
        for /f "tokens=*" %%i in (%USERPROFILE%\.rakan\.installation_info) do set "EXISTING_INSTALL=%%i"
        echo Previous installation: %%i
        echo Proceeding with reinstallation...
        echo.
    )
) else (
    REM Check if data directory exists but no marker
    if exist "%USERPROFILE%\.rakan\models" (
        echo Found existing RAKAN data directory.
        echo This contains your models, logs, and configuration.
        echo.
        echo This is not a duplicate installation - the data directory
        echo is shared across installations. This is safe to continue.
        echo.
        echo Proceeding with installation...
        echo Your existing data will be preserved.
        echo.
    )
)

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

REM Create installation marker
if not exist "%USERPROFILE%\.rakan" mkdir "%USERPROFILE%\.rakan"
echo %RAKAN_DIR% > "%USERPROFILE%\.rakan\.installation_info"
echo Installation marker created: %USERPROFILE%\.rakan\.installation_info
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