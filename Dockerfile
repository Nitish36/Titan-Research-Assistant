# 1. Use a slim official Python runtime
FROM python:3.11-slim

# 2. Install native system-level dependencies required for headless Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    wget \
    gnupg \
    libgconf-2-4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgdk-pixbuf2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the application directory
WORKDIR /app

# 4. Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Tell Playwright to download the Chromium browser binary
RUN playwright install chromium

# 6. Copy all your application files
COPY . .

# 7. Expose Chainlit's standard port
EXPOSE 8000

# 8. Start Chainlit and bind it to 0.0.0.0 so Render can route public traffic to it
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
