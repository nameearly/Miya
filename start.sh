#!/bin/bash

echo ================================================================================
echo                        MIYA AI SYSTEM LAUNCHER
echo                             Version 4.0
echo ================================================================================
echo.
echo Select startup mode:
echo.
echo   [1] Terminal Client  - Command Line Terminal
echo   [2] Web Client       - Web Interface
echo   [3] Desktop Client   - Electron Desktop App
echo   [4] QQ Client        - QQ Bot
echo   [5] All Clients      - Terminal + Web + Desktop + QQ
echo.
echo   [0] Exit
echo.
read -p "Enter choice [0-5]: " choice

case $choice in
    1)
        echo "Starting Terminal Client..."
        python3 run/multi_terminal_main_v2.py
        ;;
    2)
        echo "Starting Web Client..."
        python3 run/web_main.py
        ;;
    3)
        echo "Starting Desktop Client..."
        cd frontend/packages/desktop
        npm run dev
        ;;
    4)
        echo "Starting QQ Client..."
        python3 run/qq_main.py
        ;;
    5)
        echo "Starting All Clients..."
        python3 run/runtime_api_start.py &
        sleep 2
        python3 webnet/web_main.py &
        sleep 2
        cd frontend/packages/desktop && npm run dev &
        python3 run/multi_terminal_main_v2.py
        ;;
    0)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac
