#!/bin/bash
# Start LibreOffice in headless mode for LeenO MCP Server
# This script must be run before starting the MCP server

echo "Starting LibreOffice in headless mode..."

# Find soffice executable
SOFFICE=""

# Check common paths
if [ -x "/usr/bin/soffice" ]; then
    SOFFICE="/usr/bin/soffice"
elif [ -x "/usr/local/bin/soffice" ]; then
    SOFFICE="/usr/local/bin/soffice"
elif [ -x "/opt/libreoffice/program/soffice" ]; then
    SOFFICE="/opt/libreoffice/program/soffice"
elif [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]; then
    # macOS
    SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"
elif command -v soffice &> /dev/null; then
    SOFFICE="soffice"
fi

if [ -z "$SOFFICE" ]; then
    echo "ERROR: LibreOffice not found!"
    echo "Please install LibreOffice or set SOFFICE environment variable."
    exit 1
fi

echo "Found LibreOffice: $SOFFICE"
echo ""
echo "Starting with socket listener on port 2002..."
echo "Press Ctrl+C to stop."
echo ""

"$SOFFICE" --headless --accept="socket,host=localhost,port=2002;urp;StarOffice.ComponentContext"
