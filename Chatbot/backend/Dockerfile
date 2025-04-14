# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are needed - e.g., for certain ML libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends <packages> && rm -rf /var/lib/apt/lists/*

# Install NLTK data (needed for index_to_chroma.py)
# We run this separately as it downloads data, not just installs packages
RUN pip install --no-cache-dir nltk && \
    python -m nltk.downloader punkt && \
    python -m nltk.downloader punkt_tab

# Install Python dependencies
# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
# Use the "reload" flag for development, remove it for production
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "5000"]
# For development with reload:
# CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "5000", "--reload"] 