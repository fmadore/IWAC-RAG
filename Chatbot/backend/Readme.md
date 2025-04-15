# IWAC RAG Chatbot: Backend Service

This directory contains the code for the backend service of the IWAC RAG Chatbot, featuring a modular architecture that supports multiple LLM providers.

## Architecture

The backend uses a layered architecture with the following components:

### 1. API Layer (`app/api.py`)

The FastAPI application that exposes endpoints for:
- `/query` - Main RAG endpoint for answering questions
- `/models` - Lists available LLM models
- `/filters` - Provides filter options based on document metadata

### 2. Model Layer (`app/models/`)

A modular system for managing different LLM providers:

- **ModelManager** (`app/models/__init__.py`): Central coordinator that:
  - Loads model configurations from JSON
  - Instantiates appropriate provider classes
  - Routes requests to the correct provider
  - Provides a unified interface for model operations

- **Provider Classes**:
  - `base.py` - Abstract base class defining the LLM provider interface
  - `ollama_provider.py` - Implementation for local Ollama models
  - `gemini_provider.py` - Implementation for Google's Gemini models
  - `openai_provider.py` - Implementation for OpenAI's GPT models

### 3. Configuration (`app/config/`)

- `model_configs.json` - Defines available models with their settings:
  - Context window sizes
  - Temperature settings
  - Provider-specific parameters

### 4. Data Processing (`scripts/`)

- `index_to_chroma.py` - Tool for processing article data and creating vector embeddings in ChromaDB

## Setup & Installation

Dependencies are listed in `requirements.txt`. When using Docker (recommended), dependencies are installed automatically during the image build process based on the `Dockerfile`.

For local development (outside Docker):
```bash
pip install -r requirements.txt
# Ensure NLTK data is downloaded (handled in Dockerfile)
python -m nltk.downloader punkt
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
Ensure ChromaDB and your chosen LLM provider are running and accessible.
```bash
# Navigate to the backend directory if not already there
cd Chatbot/backend 
# Run uvicorn (adjust host/port/reload as needed)
uvicorn app.api:app --host 0.0.0.0 --port 5000 --reload 
```

## Environment Variables

The backend uses the following environment variables (typically set via a `.env` file in the main `Chatbot` directory and loaded by `docker-compose.yml`):

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `CHROMADB_HOST` | ChromaDB server hostname | `localhost` | Yes |
| `CHROMADB_PORT` | ChromaDB server port | `8000` | Yes |
| `COLLECTION_NAME` | ChromaDB collection name | `iwac_articles` | Yes |
| `EMBEDDING_MODEL_NAME` | SentenceTransformer model | `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | Yes |
| `MODEL_NAME` | Default LLM model to use | `gemma3:4b` | Yes |
| `OLLAMA_BASE_URL` | URL for Ollama API | `http://ollama:11434` | Only for Ollama |
| `EXTERNAL_API_KEY` | API key for external providers | - | For Gemini/OpenAI |

## Adding New Models

To add a new model to the system:

1. Edit `app/config/model_configs.json` and add your model configuration:
   ```json
   {
     "id": "your-new-model-id",
     "name": "Display Name for Your Model",
     "provider": "provider_name",
     "context_window": 8192,
     "temperature": 0.1,
     "options": {
       "param1": "value1",
       "param2": "value2"
     }
   }
   ```

2. If adding a new provider type, create a new provider class in `app/models/` by:
   - Creating a new file like `new_provider.py`
   - Implementing the `LLMProvider` abstract class
   - Adding the provider to the `_initialize_providers` method in `ModelManager`

## API Endpoints

### `/query` (POST)

Main endpoint for RAG query processing.

**Request:**
```json
{
  "query": "What were the main topics of the Dakar conference?",
  "model_name": "gemma3:4b",
  "filters": {
    "newspaper": "Le Réveil Islamique",
    "date_range": {
      "from": "1950-01-01",
      "to": "1960-12-31"
    }
  },
  "top_k": 5
}
```

**Response:**
```json
{
  "answer": "The main topics of the Dakar conference included...",
  "sources": [
    {
      "id": "article_001_chunk_0",
      "title": "Discussions on Islamic Education in Dakar",
      "newspaper": "Le Réveil Islamique",
      "date": "1955-03-15",
      "text_snippet": "The conference hall in Dakar buzzed with activity..."
    }
  ],
  "query_time": 1.25
}
```

### `/models` (GET)

Returns available models that can be used with the `/query` endpoint.

**Response:**
```json
{
  "models": [
    {
      "id": "gemma3:4b",
      "name": "Ollama: Gemma3 4B"
    },
    {
      "id": "deepseek-r1:7b",
      "name": "Ollama: Deepseek R1 7B"
    },
    {
      "id": "gemini-pro",
      "name": "Gemini: Pro"
    }
  ]
}
```

### `/filters` (GET)

Returns available filter options for use with the `/query` endpoint.

**Response:**
```json
{
  "newspapers": ["Le Réveil Islamique", "Nigerian Citizen", "L'Essor"],
  "locations": ["Dakar", "Senegal", "Kano", "Nigeria", "Bamako", "Mali"],
  "subjects": ["Islamic education", "Tijjaniyya", "Hajj", "Pilgrimage"],
  "date_range": {
    "min": "1955-03-15",
    "max": "1970-01-20"
  }
}
```

## Model Provider System

### Provider Interface

All providers implement the `LLMProvider` interface:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate API key availability"""
        pass
```

### Provider-Specific Implementations

Each provider handles:
- API communication with the LLM service
- Error handling specific to the provider
- Authentication and API key validation
- Response extraction and formatting

## Troubleshooting

**Common Issues:**

1. **ChromaDB Connection Errors**:
   - Ensure ChromaDB is running and accessible on the specified host/port
   - Check network connectivity between containers if using Docker

2. **LLM Provider Issues**:
   - For Ollama: Ensure Ollama service is running and models are downloaded
   - For Gemini/OpenAI: Verify API key is correctly set in `.env`
   - Check `MODEL_NAME` matches an existing model in your provider

3. **Missing NLTK Data**:
   - If running outside Docker, ensure you've downloaded NLTK data:
     ```python
     python -m nltk.downloader punkt
     ```

4. **Out of Memory Errors**:
   - Reduce batch size in the indexing script
   - Adjust Docker container memory limits