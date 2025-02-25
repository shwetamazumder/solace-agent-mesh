# Stage 1: Build
FROM python:3.11-slim

WORKDIR /app

# Install only runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends plantuml graphviz git && \
    apt-get purge -y --auto-remove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . /app

# Install dependencies using secret
RUN python3.11 -m pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1


LABEL org.opencontainers.image.source https://github.com/SolaceLabs/solace-agent-mesh

ENTRYPOINT ["python", "cli/main.py"]
