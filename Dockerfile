FROM kalilinux/kali-rolling:latest

LABEL maintainer="Bottel Security Bot"
LABEL description="Kali Linux environment for cybersecurity Telegram bot"

ENV DEBIAN_FRONTEND=noninteractive

# Update and install core Kali tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Networking & Scanning
    nmap \
    masscan \
    netcat-traditional \
    tcpdump \
    traceroute \
    dnsutils \
    whois \
    # Web tools
    nikto \
    dirb \
    gobuster \
    curl \
    wget \
    # Exploitation & Analysis
    metasploit-framework \
    sqlmap \
    hydra \
    john \
    hashcat \
    # Wireless
    aircrack-ng \
    # Utilities
    python3 \
    python3-pip \
    python3-venv \
    git \
    vim \
    net-tools \
    iputils-ping \
    # Computer Use – virtual display + desktop control
    xvfb \
    x11vnc \
    xdotool \
    scrot \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Environment variables for the virtual display
ENV DISPLAY=:1
ENV DISPLAY_WIDTH=1280
ENV DISPLAY_HEIGHT=800

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy bot source
COPY bot.py computer_use.py ./

# Entrypoint: start virtual display then run the bot
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
