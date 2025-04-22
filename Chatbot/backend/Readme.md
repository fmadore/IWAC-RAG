# IWAC RAG Chatbot: Backend Service

This directory contains the code for the backend service of the IWAC RAG Chatbot. Its primary goal is to answer user questions based on a collection of newspaper articles, using a Retrieval-Augmented Generation (RAG) approach combined with various Large Language Models (LLMs).

## Architecture

The backend uses a layered architecture designed for modularity, especially around LLM integration:

### 1. API Layer (`app/api.py`)

- Provides the main web interface (using FastAPI) for the chatbot.
- Exposes endpoints like `/query` (to ask questions), `/models` (to see available LLMs), and `/filters` (to refine searches).
- Handles incoming requests, interacts with the data/model layers, and formats responses.

### 2. Model Layer (`app/models/`)

- **Core Concept:** Manages interactions with different LLMs and constructs the information sent to them.
- **ModelManager** (`app/models/__init__.py`): The central coordinator for the RAG process.
  - **Loads Configuration:** Reads model details (like context window size) from `config/model_configs.json`.
  - **Loads Full Articles:** On startup, it loads the entire content of the source articles (e.g., from `data/processed/input_articles.json`) into memory. This allows it to access the complete text of any article when needed.
  - **Orchestrates Context Generation:** This is key to the current RAG strategy:
    1. Receives metadata about relevant article *chunks* initially identified by the API layer (using ChromaDB).
    2. Determines the most relevant *articles* based on these chunks (using a simple ranking for now).
    3. Fetches the *full text* of these top articles from its in-memory store.
    4. Carefully combines the full text of these articles into a single context block, ensuring the total size fits within the selected LLM's token limit.
    5. Constructs the final prompt, inserting the full-article context alongside the user's question and instructions.
  - **Routes to Provider:** Sends the final prompt to the appropriate LLM provider (Ollama, OpenAI, Gemini, Anthropic).
  - *Trade-off:* Loading all articles increases memory usage but aims to provide richer, more complete context to the LLM compared to using only isolated chunks.

- **Provider Classes** (`ollama_provider.py`, `openai_provider.py`, etc.):
  - Each class handles the specifics of communicating with one type of LLM API (e.g., formatting requests, handling authentication, parsing responses).
  - They implement a common `LLMProvider` interface (`base.py`) for consistency.

### 3. Configuration (`app/config/`)

- `model_configs.json`: Stores settings for each available LLM, like its ID, context window size, temperature, and any provider-specific options.

### 4. Data Processing (`scripts/`)

- `index_to_chroma.py`: A preparatory script. It reads the source articles, splits them into smaller *chunks*, generates vector embeddings for each chunk, and stores these chunks and their embeddings in the ChromaDB vector database. This indexed data is used for the *initial, fast retrieval* step.

## Setup & Installation

Dependencies are listed in `requirements.txt`. When using Docker (recommended), dependencies are installed automatically during the image build process based on the `Dockerfile`.

For local development (outside Docker):
```bash
pip install -r requirements.txt
# Ensure NLTK data is downloaded (handled in Dockerfile)
python -m nltk.downloader punkt
```

## Running the Indexer

The indexer script prepares the ChromaDB database by processing articles into embeddable chunks. This is crucial for the initial retrieval step.

**Automatic Check/Indexing on Startup (Recommended):**
When the backend service starts (e.g., via `docker-compose up`), the `entrypoint.sh` script automatically runs `scripts/check_and_index.py`. This script:
1. Waits for ChromaDB to be available.
2. Checks if the configured collection (`COLLECTION_NAME`) exists and contains data.
3. If the collection is empty, it automatically runs the `scripts/index_to_chroma.py` script to populate the database using the data found at `/app/data/processed/input_articles.json` (within the container).

This means indexing usually happens automatically the first time the backend starts with an empty database.

**Manual Indexing (Optional):**
You might want to run the indexer manually for specific reasons (e.g., re-indexing with different parameters, using a different input file, or running outside Docker).

**Via Docker Compose:**
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
# Ensure the full articles JSON is accessible at the expected path
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
| `MODEL_NAME` | Default LLM model ID to use if not specified in the query. The actual default fallback might also be influenced by the `default_model` field in `model_configs.json`. | `gemma3:4b` | Yes |
| `OLLAMA_BASE_URL` | URL for Ollama API | `http://ollama:11434` | Only if using Ollama |
| `GEMINI_API_KEY` | API key for Google Gemini | - | Only if using Gemini |
| `OPENAI_API_KEY` | API key for OpenAI | - | Only if using OpenAI |
| `ANTHROPIC_API_KEY` | API key for Anthropic | - | Only if using Anthropic |

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
       "maxOutputTokens": 4096,
       "thinkingBudget": 16384
     }
   }
   ```

2. If adding a new provider type, create a new provider class in `app/models/` by:
   - Creating a new file like `new_provider.py`
   - Implementing the `LLMProvider` abstract class
   - Adding the provider to the `_initialize_providers` method in `ModelManager`

## API Endpoints

### `/query` (POST)

Handles user questions using the RAG process. The workflow aims to balance precise retrieval with comprehensive context:

1.  **Initial Retrieval (Chunk-based):** The user's query is compared against the indexed *chunks* in ChromaDB to quickly find the most semantically similar text segments. This identifies *potentially* relevant articles.
2.  **Metadata Transfer:** The metadata (including article IDs) of these top-matching chunks is passed to the `ModelManager`.
3.  **Full Article Selection:** The `ModelManager` identifies the unique articles these chunks belong to and selects the top-ranked ones.
4.  **Context Building (Full Article):** The `ModelManager` retrieves the *complete text* of the selected articles from its in-memory store.
5.  **Token-Aware Concatenation:** It carefully combines the full text of these articles, adding one article at a time until the context nears the token limit of the chosen LLM (reserving space for the prompt structure and expected output).
6.  **LLM Prompting:** The final prompt, containing the user query and the concatenated *full article texts* as context, is sent to the LLM for answer generation.
7.  **Response Generation:** The LLM generates the answer based *only* on the provided context. The backend returns the answer, source snippets (from the initial chunks), query time, and the number of tokens used in the final prompt sent to the LLM.

*Note:* For models with large context windows, the system retrieves more initial chunks (step 1) to provide a wider selection of potentially relevant articles for step 3.
*Limitation:* Filtering by `locations` and `subjects` in the initial retrieval (step 1) is currently limited because these fields are stored as JSON strings in the metadata. The filtering logic in `api.py` currently bypasses these fields in the database query.

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
    { // Sources still show snippets from the *initially retrieved chunks* for quick reference
      "id": "article_001_chunk_0",
      "title": "Discussions on Islamic Education in Dakar",
      "newspaper": "Le Réveil Islamique",
      "date": "1955-03-15",
      "text_snippet": "The conference hall in Dakar buzzed with activity..."
    }
  ],
  "query_time": 1.25,
  "prompt_token_count": 3850
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
    // ... other configured models
  ]
}
```

### `/filters` (GET)

Returns available filter options for use with the `/query` endpoint, based on metadata found in the indexed chunks.

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
   - For Gemini/OpenAI/Anthropic: Verify the respective API key (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) is correctly set in `.env`.
   - Check `MODEL_NAME` matches an existing model in your provider
   - Ensure the installed version of the provider's SDK (e.g., `google-generativeai`) supports all configured options (like `thinkingBudget`/`ThinkingConfig`). If not, update the library or remove the unsupported option from `model_configs.json`.

3. **Missing NLTK Data**:
   - This should be handled by the `Dockerfile`. If you encounter errors locally, ensure NLTK data is downloaded:
     ```python
     python -m nltk.downloader punkt
     ```

4. **Out of Memory Errors**:
   - The backend now loads the full article JSON into memory on startup. If `input_articles.json` is very large, the container might exceed its memory limits. Monitor usage or consider alternative data access strategies (e.g., database lookups) if necessary.
   - Indexing might also consume memory; reduce batch size if needed.
   - Adjust Docker container memory limits in `docker-compose.yml`.

5. **File Not Found for Full Articles**:
   - Verify `input_articles.json` is correctly mounted into the container (default: `./data:/app/data` in `docker-compose.yml`) and accessible at the path expected by `ModelManager` (`/app/data/processed/input_articles.json` by default).