# Use the official Ollama image
FROM ollama/ollama:latest

# Copy the custom entrypoint script
COPY entrypoint.sh /entrypoint.sh
# Ensure it has execute permissions within the image (important for Linux containers)
RUN chmod +x /entrypoint.sh

# The base image already sets up Ollama and exposes port 11434.
# No further configuration needed here for a basic setup.

# Set the custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]

# Models will be pulled by the entrypoint script after the container starts.
# Default CMD from base image is overridden by the entrypoint. 