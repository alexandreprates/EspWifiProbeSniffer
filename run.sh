#!/bin/bash

[ -z "$1" ] && { echo "Uso: $0 <env_name>"; exit 1; }
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
echo "Compilando e enviando o firmware para o dispositivo..."
platformio run --environment $1 --silent
platformio run --target upload --environment $1 --silent 2&>/dev/null
echo "Iniciando monitoramento da porta serial..."
platformio device monitor --environment $1 --quiet --filter print > $LOGNAME

echo "=== ANÁLISE DE PROBES ==="
if [ -s "$LOGNAME" ]; then
    python ./tools/analyze_probes.py $LOGNAME
else
    echo "Arquivo de log vazio ou não encontrado. Pulando análise."
fi
