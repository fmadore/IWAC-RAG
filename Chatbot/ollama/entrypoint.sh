#!/bin/sh
set -e

# Start Ollama server in the background
ollama serve &

# Get the process ID of the server
pid=$!

# Wait a bit for the server to be ready
# A more robust check would ping the API endpoint, but sleep is simpler for now
sleep 5

echo "Pulling gemma3:4b..."
ollama pull gemma3:4b

echo "Pulling deepseek-r1:7b..."
# Adjust tag if necessary
ollama pull deepseek-r1:7b

echo "Model pulling complete. Ollama server is running."

# Wait for the Ollama server process to exit
# This keeps the container running
wait $pid 