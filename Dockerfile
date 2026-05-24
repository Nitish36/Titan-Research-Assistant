# 1. Use Microsoft's official Playwright Python base image 
# This comes pre-packaged with Python, browsers, and all system libraries
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# 2. Set the application directory
WORKDIR /app

# 3. Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all your application files
COPY . .

# 5. Expose Chainlit's standard port
EXPOSE 8000

# 6. Start Chainlit and bind it to 0.0.0.0
CMD ["chainlit", "run", "app.py", "--host", "0.0.0.0", "--port", "8000"]
