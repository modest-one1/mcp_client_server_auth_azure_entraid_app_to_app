FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose mcp port

EXPOSE 8080 8000

# log message
RUN echo "Starting MCP Server on port 8080"

# run mcp server server.py file
CMD ["python", "server.py"]
