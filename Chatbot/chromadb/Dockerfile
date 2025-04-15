# Start from the official ChromaDB image
FROM ghcr.io/chroma-core/chroma:latest

# Switch to root user to install packages
USER root

# Install curl
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Switch back to the default chroma user (optional, but good practice if the base image uses one)
# You might need to check the base image Dockerfile or experiment if this causes issues.
# USER chroma 