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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy bot source
COPY bot.py .

CMD ["python3", "bot.py"]
