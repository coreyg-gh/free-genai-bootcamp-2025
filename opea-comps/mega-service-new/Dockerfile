# Use specific Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN useradd -m appuser && \
    chown appuser:appuser /app

# Install only required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY /app/. .

# Set ownership of application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8888

# Command to run the application
CMD ["python", "chat.py"]