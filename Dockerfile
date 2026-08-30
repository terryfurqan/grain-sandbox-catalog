# ==============================================================================
# GRAIN Sandbox Experiment Data Server - Docker Containerfile
# Fully compatible with Hugging Face Spaces (Port 7860, Non-Root UID 1000)
# and standard Cloud Web Services (Render.com, Railway, Fly.io, Local Docker)
# ==============================================================================
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (UID 1000) for Hugging Face Spaces compliance & security
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR /app

# Ensure directory permissions for user 1000
RUN chown -R user:user /app

# Switch to non-root user
USER user

# Copy and install python dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY --chown=user:user app/ ./app/
COPY --chown=user:user .env.example ./.env.example

# Expose default port (7860 for Hugging Face Spaces)
EXPOSE 7860

# Health check (dynamically evaluates PORT environment variable)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, os; port=os.environ.get('PORT', '7860'); urllib.request.urlopen(f'http://localhost:{port}/api/stats').read()" || exit 1

# Start the application using Uvicorn (reads $PORT or defaults to 7860)
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
