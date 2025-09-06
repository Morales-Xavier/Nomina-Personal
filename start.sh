#!/bin/bash
set -e

# Iniciar servidor gráfico virtual
Xvfb :1 -screen 0 1440x900x24 &

export DISPLAY=:1
sleep 1

# Window manager
fluxbox &

# Ejecutar tu app
python3 "Nomina de Personal.py" &

# Iniciar servidor VNC
x11vnc -display :1 -nopw -forever -shared -rfbport 5900 &

# Iniciar noVNC 
/opt/noVNC/utils/novnc_proxy --vnc localhost:5900 --listen 6901 &

# Mantener vivo
wait
