#!/bin/zsh
cd "$(dirname "$0")"

echo "====================================="
echo "  Saark Enterprise Management System"
echo "====================================="
echo

echo "Starting Task Manager..."
echo

export APP_AUTO_LOGIN=1
export APP_USERNAME=admin
export APP_PASSWORD=admin123
export APP_OPEN_TASK_MANAGER=1

if command -v python3 >/dev/null 2>&1; then
    python3 main.py
else
    python main.py
fi

exit_status=$?
if [ "$exit_status" -ne 0 ]; then
    echo
    echo "[ERROR] Desktop application closed unexpectedly."
    read -r "?Press Enter to exit... "
fi

exit "$exit_status"
