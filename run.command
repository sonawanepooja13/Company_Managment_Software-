#!/bin/zsh
# =====================================
#   Saark Enterprise Management System
#   macOS Launcher (Desktop + Web)
# =====================================

# Always run from the folder containing this script
cd "$(dirname "$0")" || exit 1

echo "====================================="
echo "  Saark Enterprise Management System"
echo "====================================="
echo
echo "Choose Application Type:"
echo "  1. Desktop Application (main.py)"
echo "  2. Web Application (saarkweb.py)"
echo
printf "Enter your choice (1 or 2): "
read -r choice

# Pick the python interpreter available on this Mac
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo
    echo "[ERROR] Python is not installed or not on PATH."
    echo "Install Python 3 (https://www.python.org/downloads/) and try again."
    echo
    printf "Press Enter to exit... "
    read -r
    exit 1
fi

case "$choice" in
    1)
        echo
        echo "====================================="
        echo "  Starting Desktop Application"
        echo "====================================="
        echo
        echo "Access: Desktop GUI Application"
        echo

        # Optional auto-login (matches the existing run1.command / run2.command)
        export APP_AUTO_LOGIN=1
        export APP_USERNAME=admin
        export APP_PASSWORD=admin123

        "$PYTHON_BIN" "main.py"
        status=$?

        if [ "$status" -ne 0 ]; then
            echo
            echo "[ERROR] Desktop application closed unexpectedly."
            printf "Press Enter to exit... "
            read -r
        fi
        exit "$status"
        ;;
    2)
        echo
        echo "====================================="
        echo "  Starting Web Application"
        echo "====================================="
        echo
        echo "Username: a"
        echo "Password: a"
        echo
        echo "Local Access: http://127.0.0.1:5000"
        echo
        echo "Press CTRL+C to stop the web server"
        echo "====================================="
        echo

        "$PYTHON_BIN" "saarkweb.py"
        status=$?

        if [ "$status" -ne 0 ]; then
            echo
            echo "[ERROR] Web server closed unexpectedly."
            printf "Press Enter to exit... "
            read -r
        fi
        exit "$status"
        ;;
    *)
        echo
        echo "Invalid choice. Please enter 1 or 2."
        printf "Press Enter to exit... "
        read -r
        exit 1
        ;;
esac
