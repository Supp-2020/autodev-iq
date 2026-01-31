# Start from Python base
FROM python:3.10-slim

# Install system dependencies: Node.js 20 + Docker CLI + Puppeteer deps
RUN apt-get update && apt-get install -y \
    curl \
    git \
    gnupg \
    apt-transport-https \
    ca-certificates \
    lsb-release \
    # Install Node.js 20
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    # Install Docker CLI
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list \
    && apt-get update && apt-get install -y docker-ce-cli \
    # Install Puppeteer/Chromium dependencies for BackstopJS
    && apt-get install -y \
       chromium \
       chromium-sandbox \
       fonts-liberation \
       libasound2 \
       libatk1.0-0 \
       libcups2 \
       libdbus-1-3 \
       libdrm2 \
       libgbm1 \
       libgtk-3-0 \
       libnspr4 \
       libnss3 \
       libx11-xcb1 \
       libxcomposite1 \
       libxdamage1 \
       libxext6 \
       libxfixes3 \
       libxrandr2 \
       libxshmfence1 \
       libxss1 \
       libxtst6 \
       xdg-utils \
    # Clean up apt cache to reduce image size
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# ---------- Python dependencies layer ----------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium  # ✅ Install Playwright browser

# ---------- Node.js dependencies layer ----------
COPY package.json package-lock.json* ./
RUN npm install

# ---------- App source code ----------
COPY . .

# Expose Python backend port
EXPOSE 8000

# Start backend
CMD ["python", "main.py"]
