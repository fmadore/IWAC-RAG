# Backend Service README

This directory contains the code for the backend service of the IWAC RAG Chatbot.

## Purpose

The backend service is responsible for:
1.  **Indexing Data:** Running the `index_to_chroma.py` script to process the input JSON data, generate embeddings, and store them in the ChromaDB vector database.
2.  **API Server:** Running a FastAPI application (`app/api.py`) that handles user queries, interacts with ChromaDB and the chosen Language Model (LLM), and provides results to the frontend.

## Structure

-   `app/api.py`: The main FastAPI application code.
-   `scripts/index_to_chroma.py`: Script to index data into ChromaDB.
-   `Dockerfile`: Instructions to build the Docker image for the backend service.
-   `requirements.txt`: Python dependencies for the backend.

## Setup & Installation

Dependencies are listed in `requirements.txt`. When using Docker (recommended), dependencies are installed automatically during the image build process based on the `Dockerfile`.

For local development (outside Docker):
```bash
pip install -r requirements.txt
# Ensure NLTK data is downloaded (handled in Dockerfile)
# python -m nltk.downloader punkt fr 
```

## Running the Indexer

The indexer script populates the ChromaDB database.

**Via Docker Compose (Recommended):**
Make sure your input JSON file (e.g., `../data/processed/input_articles.json`) is ready. Run the following from the main `Chatbot` directory:
```bash
docker-compose run --rm backend python app/scripts/index_to_chroma.py --input data/processed/input_articles.json --chroma-host chromadb
```
*(Adjust `--input` path if your file is named differently. `--chroma-host chromadb` points to the ChromaDB service defined in `docker-compose.yml`)*

**Locally:**
Ensure ChromaDB is running and accessible (e.g., via Docker).
```bash
python scripts/index_to_chroma.py --input ../data/processed/input_articles.json --chroma-host localhost --chroma-port 8000
```
*(Adjust paths and host/port as needed)*

## Running the API Server

**Via Docker Compose (Recommended):**
The API server is started automatically when you run `docker-compose up` from the main `Chatbot` directory. It listens on port 5000 inside the container, which is mapped to port 5000 on the host by default in `docker-compose.yml`.

**Locally:**
Ensure ChromaDB and Ollama (if used) are running and accessible.
```bash
# Navigate to the backend directory if not already there
cd Chatbot/backend 
# Run uvicorn (adjust host/port/reload as needed)
uvicorn app.api:app --host 0.0.0.0 --port 5000 --reload 
```

## Environment Variables

The API server (`app/api.py`) uses the following environment variables (typically set via a `.env` file in the main `Chatbot` directory and loaded by `docker-compose.yml`):

-   `OLLAMA_BASE_URL`: URL of the Ollama service (e.g., `http://ollama:11434`).
-   `CHROMADB_HOST`: Hostname of the ChromaDB service (e.g., `chromadb`).
-   `CHROMADB_PORT`: Port of the ChromaDB service (e.g., `8000`).
-   `COLLECTION_NAME`: Name of the ChromaDB collection to use (e.g., `iwac_articles`).
-   `LLM_PROVIDER`: Specifies the LLM provider ('ollama', 'gemini', 'openai'). Defaults to 'ollama'.
-   `MODEL_NAME`: The specific model name to use with the LLM provider (e.g., 'llama3', 'gemma3:4b').
-   `EMBEDDING_MODEL_NAME`: The Sentence Transformer model for embeddings (e.g., 'all-MiniLM-L6-v2').
-   `EXTERNAL_API_KEY`: API key required if `LLM_PROVIDER` is set to 'gemini' or 'openai'. 