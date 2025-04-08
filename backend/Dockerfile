FROM python:3.11-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies directly
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir PyJWT

# Create non-root user for security
RUN addgroup --system appuser && \
    adduser --system --group appuser && \
    mkdir -p /app/static/temp /app/static/uploads && \
    mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appuser /app && \
    chown -R appuser:appuser /home/appuser

# Copy application code
COPY . .
RUN chown -R appuser:appuser /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app:${PATH}" \
    HF_HOME="/home/appuser/.cache/huggingface"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]