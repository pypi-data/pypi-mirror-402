@echo off
REM Start LibreOffice in headless mode for LeenO MCP Server
REM This script must be run before starting the MCP server

echo Starting LibreOffice in headless mode...

REM Try common LibreOffice installation paths
set SOFFICE_PATH=

REM Check Program Files
if exist "C:\Program Files\LibreOffice\program\soffice.exe" (
    set SOFFICE_PATH=C:\Program Files\LibreOffice\program\soffice.exe
)

REM Check Program Files (x86)
if exist "C:\Program Files (x86)\LibreOffice\program\soffice.exe" (
    set SOFFICE_PATH=C:\Program Files (x86)\LibreOffice\program\soffice.exe
)

REM Check if soffice is in PATH
where soffice >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set SOFFICE_PATH=soffice
)

if "%SOFFICE_PATH%"=="" (
    echo ERROR: LibreOffice not found!
    echo Please install LibreOffice or set SOFFICE_PATH environment variable.
    exit /b 1
)

echo Found LibreOffice: %SOFFICE_PATH%
echo.
echo Starting with socket listener on port 2002...
echo Press Ctrl+C to stop.
echo.

"%SOFFICE_PATH%" --headless --accept="socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
