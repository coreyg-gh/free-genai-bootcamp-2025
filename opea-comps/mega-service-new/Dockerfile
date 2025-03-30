# Use Python 3.10 slim image
FROM python:3.10-slim

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
COPY ./app/requirements.txt .

# Install dependencies with specific versions
RUN pip install --no-cache-dir -r requirements.txt

# Find the correct path to pushpull.py and modify it
RUN DOCARRAY_PATH=$(python -c "import sys; try: import docarray; import os; print(os.path.dirname(docarray.__file__)); except Exception: sys.exit(0)") || true && \
    if [ -n "$DOCARRAY_PATH" ]; then \
        sed -i 's/def _get_cloud_api():/def _get_cloud_api():\n    return ""/g' "$DOCARRAY_PATH/array/mixins/io/pushpull.py"; \
    fi

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
