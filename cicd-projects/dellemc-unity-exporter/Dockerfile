FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip --index-url http://vnk-nexus.abramad.com/repository/pypi-proxy/simple --trusted-host vnk-nexus.abramad.com
RUN pip install --no-cache-dir -r requirements.txt --index-url http://vnk-nexus.abramad.com/repository/pypi-proxy/simple --trusted-host vnk-nexus.abramad.com

# Copy application
COPY dellemc_unity_exporter.py .

# Expose exporter port
EXPOSE 9105

# Default values (can be overridden by .env)
ENV EXPORTER_WORKERS=2
ENV EXPORTER_THREADS=2

# Run gunicorn using env variables
CMD gunicorn \
    -w ${EXPORTER_WORKERS} \
    -k gthread \
    --threads ${EXPORTER_THREADS} \
    -b 0.0.0.0:9105 \
    dellemc_unity_exporter:app
