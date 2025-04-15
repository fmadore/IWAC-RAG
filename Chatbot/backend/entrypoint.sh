#!/bin/sh
# Entrypoint script for the backend service

# Exit immediately if a command exits with a non-zero status.
set -e

# Run the check and index script
# This script will exit with 0 if successful (indexing done or skipped)
# or non-zero if connection/indexing fails.
echo "--- Running check_and_index.py script --- "
python /app/scripts/check_and_index.py

# If the check script succeeded (exit code 0), start the main application
echo "--- Starting Uvicorn server --- "
exec uvicorn app.api:app --host 0.0.0.0 --port 5000 