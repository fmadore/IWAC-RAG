# IWAC-RAG: Islam West Africa Collection - Retrieval Augmented Generation

This repository contains the code for a RAG (Retrieval Augmented Generation) system that provides an interactive chatbot interface for querying the Islam West Africa Collection archives.

## System Overview

The IWAC-RAG system consists of several components:

1. **Vector Database**: ChromaDB stores vector embeddings of article chunks for efficient semantic retrieval.
2. **LLM Service**: Flexible architecture supporting multiple LLM providers (Ollama, Gemini, OpenAI).
3. **Backend API**: FastAPI service that handles query processing, retrieval, and LLM generation.
4. **Frontend UI**: Interactive SvelteKit user interface for querying and displaying results.

## Backend Architecture

The backend uses a modular architecture with the following components:

### Model Management

- **ModelManager**: Central coordinator that loads configurations and routes requests to appropriate providers.
- **LLM Providers**: Separate modules for each supported LLM service (Ollama, Gemini, OpenAI).
- **Configuration**: Models and their settings (context window, temperature, etc.) defined in JSON.

### API Endpoints

- **`/query`**: Main endpoint that performs RAG retrieval and response generation.
- **`/models`**: Provides information about available models.
- **`/filters`**: Returns metadata for filtering search results (newspapers, dates, etc.).

## Getting Started

### Prerequisites

- Docker and Docker Compose
- (Optional) API keys for external LLMs (Gemini, OpenAI)

### Configuration

1. Copy `.env.example` to `.env` and configure your environment:

```bash
cp Chatbot/.env.example Chatbot/.env
```

2. Edit the `.env` file to set your preferences:
   - Select LLM provider (`OLLAMA`, `GEMINI`, or `OPENAI`)
   - Configure API keys for external providers
   - Set default model

### Running with Docker Compose

1. Start all services:

```bash
cd Chatbot
docker-compose up -d
```

2. Index your article data (first time only):

```bash
docker-compose exec backend python scripts/index_to_chroma.py
```

3. Access the frontend at: http://localhost:3000

## Using Multiple Models

The system supports switching between different LLM models at runtime:

- Local models via Ollama (gemma3:4b, deepseek-r1:7b, etc.)
- Google's Gemini models (requires API key)
- OpenAI models (requires API key)

You can select the model in the UI or configure a default in the `.env` file.

## Adding New Models

To add a new model:

1. Edit `backend/app/config/model_configs.json` to add your model configuration.
2. If adding a new provider type, create a new provider class in `backend/app/models/`.

## Development

### Local Development Setup

For local development without Docker:

1. Set up Python environment for backend:

```bash
cd Chatbot/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up Node.js environment for frontend:

```bash
cd Chatbot/frontend
npm install
```

3. Run services locally:
   - ChromaDB (via Docker or local install)
   - Ollama (if using local models)
   - Backend: `uvicorn app.api:app --reload`
   - Frontend: `npm run dev`

## Environment Variables

Key environment variables (set in `.env`):

- `LLM_PROVIDER`: The LLM service to use (`ollama`, `gemini`, or `openai`)
- `MODEL_NAME`: Default model ID to use
- `EXTERNAL_API_KEY`: API key for Gemini or OpenAI
- `OLLAMA_BASE_URL`: URL for the Ollama service
- `CHROMADB_HOST`: ChromaDB host
- `CHROMADB_PORT`: ChromaDB port (default: 8000)
- `COLLECTION_NAME`: Name of the ChromaDB collection
- `EMBEDDING_MODEL_NAME`: Model used for generating vector embeddings

## License

[Your license information here]

## 1. Environment Setup

### 1.1 Prerequisites
- [ ] Server environment (Linux or Windows) with Docker and Docker Compose installed and compatible with the host OS.
- [ ] Adequate storage for vector embeddings (~2-5GB depending on embedding model)
- [ ] Sufficient RAM for running local Ollama models if used (minimum 8GB, recommended 16GB+)
- [ ] API keys for external LLM providers (e.g., Gemini, Claude, OpenAI) stored securely if used.
- [x] Input JSON file containing pre-processed article data (See Section 2.1).

### 1.2 Project Structure
- [x] Create Project Directory Structure (as defined below)
```
Chatbot/
├── docker-compose.yml
├── .env
├── data/
│   ├── processed/       # Location for the input JSON file (e.g., input_articles.json)
│   └── vectors/         # Persistent storage for ChromaDB vectors
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   └── api.py         # Main FastAPI application
│   └── scripts/
│       └── index_to_chroma.py # Script to load JSON and index to ChromaDB
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── svelte.config.js
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── postcss.config.js
    ├── tsconfig.json
    ├── src/
    │   ├── routes/
    │   │   └── +page.svelte # Main UI page
    │   ├── components/
    │   │   ├── ChatMessage.svelte
    │   │   ├── FilterPanel.svelte
    │   │   └── SourcePanel.svelte
    │   └── app.html       # Main HTML shell
    └── static/
```
*Note: Simplified structure shown. Actual frontend has more config files (ESLint, Prettier, etc.).*

### 1.3 Docker Setup
- [x] Create `docker-compose.yml` file (basic structure)
- [x] Create `Chatbot/backend/Dockerfile`
- [x] Create `Chatbot/frontend/Dockerfile` (template, may need adjustments)
- [x] Create `Chatbot/ollama/Dockerfile` (basic)
- [ ] Configure environment variables in `.env` file

## 2. Data Processing (Simplified)

### 2.1 Input Data Preparation (Pre-requisite)
- [x] Define expected input JSON structure.
- [x] Create mock `input_articles.json` file.
- The system expects a pre-processed JSON file located in `Chatbot/data/processed/` (e.g., `input_articles.json`).
- Each object in the JSON array should have the following structure:
  ```json
  {
    "id": "unique_article_id", 
    "title": "Article Title", 
    "newspaper": "Newspaper Name", 
    "date": "YYYY-MM-DD", 
    "subject": ["keyword1", "person", "topic"], 
    "spatial": ["location1", "city", "country"], 
    "summary": "Pre-generated summary of the article.", 
    "content": "Full text content of the article."
  }
  ```

### 2.2 Vectorization Pipeline
- [x] Develop script `index_to_chroma.py` to process the input JSON file.
- [x] Design chunking strategy (basic NLTK sentence chunking implemented)
  - [x] Consider semantic boundaries (basic sentence boundaries used)
  - [x] Determine optimal chunk size (parameterized, default 512)
  - [x] Handle metadata inclusion in chunks (implemented, maps `subject`->`subjects`, `spatial`->`locations`)
- [x] Generate embeddings for each chunk (using SentenceTransformer)
- [x] Store embeddings in ChromaDB (code present)
- [ ] Implement metadata filtering capabilities (basic filtering in API, needs review for list fields)

## 3. RAG System Implementation

### 3.1 Vector Database Setup
- [x] Configure ChromaDB in Docker (`docker-compose.yml`)
  - [x] Set up persistent storage (volume defined)
  - [ ] Configure authentication (not implemented)
  - [ ] Optimize for performance (defaults used)

### 3.2 Language Model Configuration
- **Option 1: Local Ollama Setup**
  - [x] Create a Dockerfile for Ollama (`Chatbot/ollama/Dockerfile` - basic)
  - [ ] Pull appropriate models (manual step or in Dockerfile)
  - [ ] Configure model parameters (basic options in `api.py`)
- **Option 2: External LLM API Setup**
  - [ ] Securely store API keys in the `.env` file.
  - [x] Implement logic in the backend to use the specified provider and key (placeholders in `api.py`)

### 3.3 RAG Pipeline
- [x] Develop core RAG functionality in `api.py`:
  - [x] Question processing (basic input handling)
  - [x] Relevant document retrieval (ChromaDB query)
  - [x] Context creation (joining retrieved docs)
  - [ ] Query augmentation (not implemented)
  - [x] Response generation using Ollama (implemented)
  - [ ] Response generation using external APIs (placeholders exist)
  - [x] Source tracking and citation (basic source list returned)

### 3.4 API Development
- [x] Design and implement RESTful API (`api.py` using FastAPI)
  - [x] `/query` endpoint for chatbot interactions
  - [ ] `/sources` endpoint for cited documents (sources returned by `/query`)
  - [ ] `/feedback` endpoint for user feedback (not implemented)
  - [x] `/filters` endpoint for available filter options
  - [ ] Authentication and rate limiting (not implemented)

## 4. Web Interface Development

### 4.1 Frontend Framework Setup
- [x] Set up Svelte with SvelteKit:
  - [x] Project initialization (using `npm create svelte@latest .`)
  - [x] Component structure (basic files created)
  - [x] API integration (fetch calls in `+page.svelte`)
  - [x] Add Tailwind CSS (via `svelte-add`)
  - [x] Add Tailwind plugins (`@tailwindcss/typography`, `@tailwindcss/forms`)
  - [ ] Responsive design foundation (requires Tailwind/CSS setup)

### 4.2 UI Components
- [x] Develop key components (placeholders/basic versions created):
  - [x] Chat interface with message history (`+page.svelte`, `ChatMessage.svelte`)
  - [x] Query input (`+page.svelte`)
  - [x] Response display with citation highlighting (`ChatMessage.svelte`, `SourcePanel.svelte`)
  - [ ] Article viewer for source exploration (not implemented)
  - [x] Filters for refining searches (`FilterPanel.svelte`)

### 4.3 Responsive Design
- [ ] Implement responsive layout:
  - [ ] Mobile-first approach
  - [ ] Tablet and desktop optimizations
  - [ ] Accessibility considerations (basic ARIA added)
  - [ ] Dark/light mode support (basic classes present, needs full setup)

### 4.4 State Management and API Integration
- [x] Set up state management (Svelte local state in `+page.svelte`)
- [x] Implement API service for backend communication (fetch calls in `+page.svelte`)
- [x] Develop error handling strategies (basic try/catch in `+page.svelte`)
- [x] Add loading states and progress indicators (basic loader in `+page.svelte`)

## 5. Integration & Deployment

### 5.1 Service Integration
- [ ] Connect frontend and backend:
  - [x] Configure API endpoints (fetch calls use API_URL)
  - [ ] Set up authentication (not implemented)
  - [x] Implement error handling (basic handling in API and frontend)

### 5.2 Docker Compose Configuration
- [x] Create `docker-compose.yml` with services (ollama, chromadb, backend, frontend)
- This file defines and configures the different services (containers) that make up the application: Ollama, ChromaDB, the Python backend, and the SvelteKit frontend.
- It manages their build process, dependencies, volumes (for persistent data), environment variables, and networking.
- Refer to the `Chatbot/docker-compose.yml` file in the repository for the complete configuration details.

### 5.3 Nginx Configuration for Production
- [ ] Set up Nginx as reverse proxy:
  - [ ] SSL termination
  - [ ] Request routing
  - [ ] Caching
  - [ ] Security headers

### 5.4 CI/CD Pipeline (Optional)
- [ ] Set up GitHub Actions or similar for:
  - [ ] Automated testing
  - [ ] Building Docker images
  - [ ] Deployment to server

## 6. Testing & Optimization

### 6.1 Functional Testing
- [ ] Test RAG pipeline with various query types
- [ ] Verify source citation accuracy
- [ ] Validate filtering capabilities
- [ ] Ensure multilingual support (if applicable based on input data)

### 6.2 Performance Optimization
- [ ] Tune ChromaDB for faster retrieval
- [ ] Optimize Ollama model parameters (or external LLM usage)
- [ ] Implement caching strategies (API level, frontend level?)
- [ ] Monitor and optimize container resource usage

### 6.3 User Experience Testing
- [ ] Conduct usability testing
- [ ] Collect and incorporate feedback
- [ ] Monitor user interactions for UI improvements

## 7. Code Examples and Implementation Notes

### 7.1 ChromaDB Indexing Script (`index_to_chroma.py`)
- [x] This script reads the pre-processed JSON file (e.g., `data/processed/input_articles.json`).
- [x] It iterates through each article, chunks the `content` using NLTK sentence tokenization.
- [x] It maps the `subject` and `spatial` fields from the JSON to `subjects` and `locations` metadata fields.
- [x] It generates embeddings using a SentenceTransformer model (`all-MiniLM-L6-v2` by default).
- [x] It adds the chunks, embeddings, and metadata to the specified ChromaDB collection.
- [x] **Run using:** `docker-compose run --rm backend python app/scripts/index_to_chroma.py --input data/processed/input_articles.json --chroma-host chromadb` (adjust input path and other args if needed).

*(Code example for index_to_chroma.py - see `Chatbot/backend/scripts/index_to_chroma.py`)*

### 7.2 RAG API Implementation (`api.py`)
- [x] Provides the core backend logic using FastAPI.
- [x] `/query` endpoint:
    - Takes a user query and optional filters.
    - Queries the ChromaDB collection for relevant text chunks.
    - Constructs a context from the retrieved chunks.
    - Sends the context and query to the configured LLM (Ollama or external API).
    - Returns the LLM's answer and source information.
- [x] `/filters` endpoint:
    - Queries ChromaDB metadata to find unique values for filtering (newspapers, locations, subjects, date range).
    - Returns these options for the frontend filter panel.

*(Code example for api.py - see `Chatbot/backend/app/api.py`)*

### 7.3 Frontend UI with Svelte (`+page.svelte` and components)
- [x] Main SvelteKit page (`src/routes/+page.svelte`) orchestrates the UI.
- [x] `ChatMessage.svelte`: Displays individual user and assistant messages.
- [x] `FilterPanel.svelte`: Allows users to select filters based on options fetched from the `/filters` endpoint.
- [x] `SourcePanel.svelte`: Displays the source documents related to the assistant's answer.
- [x] Communicates with the backend API via fetch requests to `/query` and `/filters` using the `VITE_API_URL` environment variable.

*(Code example for +page.svelte and components - see `Chatbot/frontend/src/...`)*

## 8. Deployment Checklist

- [ ] Ensure Docker and Docker Compose are installed on the target server (Linux or Windows)
- [ ] Clone repository to server
- [x] Prepare the input JSON file (e.g., `Chatbot/data/processed/input_articles.json`)
- [ ] Configure environment variables in `.env`, including `LLM_PROVIDER` and `EXTERNAL_API_KEY` if using external APIs. Also ensure `VITE_API_URL` is set appropriately for the frontend build context if needed.
- [ ] Build Docker images (`docker-compose build`)
- [x] Run the indexing script (Example: `docker-compose run --rm backend python app/scripts/index_to_chroma.py --input data/processed/input_articles.json --chroma-host chromadb`)
- [ ] Start services with Docker Compose (`docker-compose up -d`)
- [ ] Configure Nginx as reverse proxy (if needed for production)
- [ ] Set up SSL with Let's Encrypt (if needed for production)
- [ ] Implement monitoring solution (e.g., Prometheus + Grafana)
- [ ] Securely manage API keys (consider Docker secrets or other vault solutions for production)
- [ ] Document API endpoints and usage

## 9. Resources and References

- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Svelte Documentation](https://svelte.dev/docs)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx as a Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Let's Encrypt](https://letsencrypt.org/docs/)