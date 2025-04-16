FROM ollama/ollama:0.6.5

# Create entrypoint directory
WORKDIR /app

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Exposing Ollama's default port
EXPOSE 11434

# Entrypoint script to pull models before starting server
ENTRYPOINT ["/app/entrypoint.sh"]