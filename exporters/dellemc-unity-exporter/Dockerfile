FROM python:3.11-slim

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip --index-url http://vnk-nexus.abramad.com/repository/pypi-proxy/simple --trusted-host vnk-nexus.abramad.com
RUN pip install --no-cache-dir -r requirements.txt --index-url http://vnk-nexus.abramad.com/repository/pypi-proxy/simple --trusted-host vnk-nexus.abramad.com

# Add service user
RUN useradd -r -s /usr/sbin/nologin -d /app exporter

# Copy application
COPY dellemc_unity_exporter.py .

# Permit user
RUN chown -R exporter:exporter /app
USER exporter

# Expose exporter port
EXPOSE 9105

# Default values (can be overridden by .env)
ENV EXPORTER_WORKERS=2
ENV EXPORTER_THREADS=2

# Run gunicorn using env variables
CMD ["sh", "-c", "gunicorn -w ${EXPORTER_WORKERS} --threads ${EXPORTER_THREADS} --timeout 15 -b 0.0.0.0:9105  dellemc_unity_exporter:app"]