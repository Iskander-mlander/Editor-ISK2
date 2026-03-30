#!/bin/bash
# Editor ISK2 - Launcher para terminal
# Ejecuta el editor desde terminal para depuración
export NO_AT_BRIDGE=1
cd "$(dirname "$0")"

echo "Iniciando Editor ISK2..."
python3 main.py "$@"
