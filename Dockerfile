FROM node:18-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    gnupg \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Lighthouse CLI globally
RUN npm install -g lighthouse

# Set up Python environment
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code AFTER installing dependencies
# This is crucial for the 'app.main:app' path to work correctly
# if 'app' is a sub-directory in your project root.
COPY . .

# Create reports directory
RUN mkdir -p /app/reports

# Set the PYTHONPATH environment variable.
# This ensures Python can find your 'app' module when running Uvicorn.
# ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Default command to run the Uvicorn application
# The '--reload' flag is generally not recommended for production
# in Docker, but it's fine for local development.
# ... (your existing Dockerfile content) ...

# Default command to run the Uvicorn application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]