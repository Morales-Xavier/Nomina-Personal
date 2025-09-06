FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Instalar certificados y actualizar repos
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && update-ca-certificates

# Instalar dependencias del sistema (Python + Tkinter + Xvfb + VNC + navegador remoto)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-tk \
    xvfb x11vnc fluxbox git wget \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir customtkinter pyBCV xlsxwriter requests

# Instalar noVNC y websockify
RUN git clone https://github.com/novnc/noVNC.git /opt/noVNC \
 && git clone https://github.com/novnc/websockify.git /opt/noVNC/utils/websockify

# Script de inicio
COPY start.sh /start.sh
RUN chmod +x /start.sh && ls -l /start.sh && head -n 5 /start.sh

EXPOSE 6901
CMD ["/start.sh"]
