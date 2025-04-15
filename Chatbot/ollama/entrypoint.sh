#!/bin/bash
set -e

# Define models to be pulled on startup
MODELS=("gemma3:4b" "deepseek-r1:7b")

echo "Starting Ollama with pre-pulling of models..."

# Start Ollama server in background
ollama serve &
SERVER_PID=$!

# Wait for server to be ready
echo "Waiting for Ollama server to start..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama API..."
    sleep 2
done
echo "Ollama server is up and running!"

# Pull models
for MODEL in "${MODELS[@]}"; do
    echo "Pulling model: $MODEL"
    ollama pull $MODEL || echo "Warning: Failed to pull $MODEL"
done

echo "Model initialization complete. Ollama is ready to use."

# Wait for the server to terminate
wait $SERVER_PID