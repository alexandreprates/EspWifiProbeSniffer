#!/bin/bash

[ -z "$1" ] && { echo -e "Usage: $0 <env_name>\nAvailable environments:\n$(platformio project config 2>/dev/null | grep "^env:" | sed 's/env:/ * /g')"; exit 1; }

LOGNAME="./data/raw/probe_data_$(date +%Y%m%d_%H%M%S).log"

echo "Checking for Python venv..."
if [ ! -d "./.venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv ./.venv
    source ./.venv/bin/activate
    pip install -r tools/requirements.txt
else
    echo "Activating existing Python virtual environment..."
    source ./.venv/bin/activate
fi

echo "=== ESP32 WiFi Probe Monitor ==="
platformio run --target clean --environment $1 --silent
echo "Compiling firmware..."
platformio run --environment $1 --silent 2&>/dev/null
echo "Uploading firmware to the device..."
platformio run --target upload --environment $1 --silent 2&>/dev/null
echo "Starting serial port monitoring..."

# Start background process to monitor log file line count every minute
(
    while true; do
        sleep 30
        if [ -f "$LOGNAME" ]; then
            LINE_COUNT=$(wc -l < "$LOGNAME")
            echo "[$(date '+%H:%M:%S')] Collected log lines: $LINE_COUNT" >&2
        fi
    done
) &
MONITOR_PID=$!

# Trap to kill background process when script exits
trap "kill $MONITOR_PID 2>/dev/null" EXIT

echo "Monitoring WiFi probes... Press CTRL+C to stop capture and analyze data."
platformio device monitor --environment $1 --quiet --filter printable > $LOGNAME

echo "=== RUN PROBE ANALYSIS ==="
if [ -s "$LOGNAME" ]; then
    python ./tools/analyze_probes.py $LOGNAME
else
    echo "Log file is empty or not found. Skipping analysis."
fi
