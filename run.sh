#!/bin/bash

[ -z "$1" ] && { echo "Uso: $0 <env_name>"; exit 1; }
LOGNAME="./data/raw/probe_data_$(date +%Y%m%d_%H%M%S).log"

echo "=== ESP32 WiFi Probe Monitor ==="
platformio run --target clean --environment $1 --silent
platformio run --target upload --environment $1 --silent
platformio device monitor --environment $1 --quiet --filter print > $LOGNAME

echo "=== ANÁLISE DE PROBES ==="
python ./tools/analyze_probes.py $LOGNAME
python ./tools/analyze_probes.py $LOGNAME --plots
