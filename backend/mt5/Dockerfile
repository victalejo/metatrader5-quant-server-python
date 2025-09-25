# Stage 1: Base image with apt packages
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

ENV TITLE=MetaTrader \
    WINEARCH=win64 \
    WINEPREFIX="/config/.wine" \
    DISPLAY=:0 \
    DEBIAN_FRONTEND=noninteractive

# Asegura carpeta y permisos
RUN mkdir -p /config/.wine \
 && chown -R abc:abc /config/.wine \
 && chmod -R 755 /config/.wine

# Paquetes base (sin upgrade) + limpiar cache
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates \
      gnupg \
      software-properties-common \
      dos2unix \
      python3-pip \
      wget \
      python3-xdg \
      netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

# WineHQ (bookworm): clave GPG y repo (sin apt-key)
RUN mkdir -p /etc/apt/keyrings \
 && wget -O /etc/apt/keyrings/winehq-archive.key https://dl.winehq.org/wine-builds/winehq.key \
 && echo "deb [signed-by=/etc/apt/keyrings/winehq-archive.key] https://dl.winehq.org/wine-builds/debian/ bookworm main" > /etc/apt/sources.list.d/winehq.list

# Habilita i386, actualiza índices e instala wine
RUN dpkg --add-architecture i386 \
 && apt-get update \
 && apt-get install -y --no-install-recommends winehq-stable \
 && rm -rf /var/lib/apt/lists/*

# Stage 2: Final image
FROM base

COPY app /app
COPY scripts /scripts
RUN dos2unix /scripts/*.sh && chmod +x /scripts/*.sh

COPY /root /
RUN touch /var/log/mt5_setup.log \
 && chown abc:abc /var/log/mt5_setup.log \
 && chmod 644 /var/log/mt5_setup.log

EXPOSE 3000 5000 5001 8001 18812
VOLUME /config
