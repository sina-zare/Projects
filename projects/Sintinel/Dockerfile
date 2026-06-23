# Dockerfile — Sintinel (client image: restic client + Python + tools)
FROM python:3.11-slim

# Build as root
USER root

# Install OS packages (restic client + tooling)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      restic \
      pv \
      openssh-client \
      procps \
      curl \
      bzip2 \
      ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Create non-root runtime user "sintinel"
ARG SINTINEL_UID=1000
ARG SINTINEL_GID=1000
RUN groupadd -g ${SINTINEL_GID} sintinel 2>/dev/null || true \
 && useradd -m -u ${SINTINEL_UID} -g ${SINTINEL_GID} -s /bin/bash sintinel || true

# Working dir for scripts
WORKDIR /opt/scripts

# Install python modules system-wide (no venv)
RUN pip3 install --no-cache-dir colorama tabulate prometheus_client

# Copy scripts and entrypoint
COPY scripts/ /opt/scripts/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh

# Make executable & give ownership to user
RUN chmod +x /usr/local/bin/entrypoint.sh \
 && chmod +x /opt/scripts/sintinel.py || true \
 && chown -R sintinel:sintinel /opt/scripts /home/sintinel

# Create runtime dirs and log path
RUN mkdir -p /opt/sintinel /var/log/sintinel \
 && chown -R sintinel:sintinel /opt/sintinel /var/log/sintinel

# Run as non-root user
#USER sintinel
ENV HOME=/home/sintinel
WORKDIR /opt/scripts

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]