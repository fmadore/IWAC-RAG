from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
import requests
import json
import os
from datetime import datetime
import logging

from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the project root .env file
load_dotenv(Path(__file__).parents[2] / '.env')

# Import our new ModelManager
from app.models import model_manager

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="IWAC RAG API", description="API for the Islam West Africa Collection RAG system")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", "8000"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "iwac_articles")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

logger.info(f"Using ChromaDB Host: {CHROMADB_HOST}:{CHROMADB_PORT}")
logger.info(f"Using Collection: {COLLECTION_NAME}")
logger.info(f"Using Embedding Model: {EMBEDDING_MODEL_NAME}")

# Initialize embedding function once at startup
try:
    logger.info(f"Initializing embedding function: {EMBEDDING_MODEL_NAME}...")
    _embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )
    logger.info("Embedding function initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize embedding function: {e}")
    # Depending on criticality, you might want to raise an exception or exit
    _embedding_function = None 

# Connect to ChromaDB
# Use a singleton pattern or dependency injection for production
_chroma_client = None
_collection = None

def get_chroma_client():
    global _chroma_client
    if (_chroma_client is None):
        logger.info("Initializing ChromaDB client...")
        try:
            _chroma_client = chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT)
            # Ping the server to ensure connection
            _chroma_client.heartbeat()
            logger.info("ChromaDB client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB at {CHROMADB_HOST}:{CHROMADB_PORT}: {e}")
            raise HTTPException(status_code=503, detail="Could not connect to ChromaDB service")
    return _chroma_client

def get_embedding_function():
    # Return the pre-initialized embedding function
    if _embedding_function is None:
        # This happens if initialization failed at startup
        raise HTTPException(status_code=500, detail="Embedding function could not be initialized.")
    return _embedding_function

def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        embedding_func = get_embedding_function()
        try:
            logger.info(f"Getting collection '{COLLECTION_NAME}'")
            _collection = client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_func)
            logger.info(f"Successfully retrieved collection '{COLLECTION_NAME}'")
        except Exception as e:
            # This might error if collection doesn't exist, which is okay for get_or_create
            logger.warning(f"Failed to get collection '{COLLECTION_NAME}', attempting to create: {e}")
            try:
                _collection = client.create_collection(name=COLLECTION_NAME, embedding_function=embedding_func)
                logger.info(f"Successfully created collection '{COLLECTION_NAME}'")
            except Exception as create_e:
                 logger.error(f"Failed to get or create collection '{COLLECTION_NAME}': {create_e}")
                 # If it truly fails, raise HTTPException
                 raise HTTPException(status_code=500, detail=f"Could not get or create ChromaDB collection '{COLLECTION_NAME}'")
    return _collection

# Data models
class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    top_k: int = Field(default=5, ge=1, le=200) # Allow requesting more docs for large contexts
    model_name: Optional[str] = None # Add optional model name

class Source(BaseModel):
    id: str
    title: str
    newspaper: Optional[str] = None # Make optional if data might be missing
    date: Optional[str] = None # Make optional if data might be missing
    url: Optional[str] = None
    text_snippet: str
    # Add score or other relevance info if needed
    # score: Optional[float] = None 

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    query_time: float

class FilterInfo(BaseModel):
    min: Optional[str] = None
    max: Optional[str] = None

class AvailableFilters(BaseModel):
    newspapers: List[str]
    locations: List[str]
    subjects: List[str]
    date_range: FilterInfo

class ModelInfo(BaseModel):
    id: str
    name: str

class ModelsResponse(BaseModel):
    models: List[ModelInfo]

# Helper function to parse metadata lists safely
def parse_json_metadata(metadata_str: Optional[str]) -> List[str]:
    if not metadata_str:
        return []
    try:
        data = json.loads(metadata_str)
        if isinstance(data, list):
            return [str(item) for item in data] # Ensure items are strings
    except json.JSONDecodeError:
        logger.warning(f"Failed to decode JSON metadata: {metadata_str}")
    return []

# API endpoints
@app.get("/")
def read_root():
    return {"status": "ok", "message": "IWAC RAG API is running"}

@app.get("/models", response_model=ModelsResponse)
def get_available_models():
    """
    Get a list of available models that can be used for querying
    """
    try:
        models = model_manager.get_available_models()
        return ModelsResponse(models=models)
    except Exception as e:
        logger.error(f"Error retrieving available models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve available models: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest, collection: chromadb.Collection = Depends(get_collection)):
    start_time = datetime.now()
    logger.info(f"Received query: '{request.query}' with filters: {request.filters} and model: {request.model_name}")
    
    try:
        # Prepare filters for ChromaDB query
        # ChromaDB `where` clause expects specific format
        where_filter = None
        if request.filters:
            # Basic validation/transformation can be added here
            # Example: ensure date format, handle specific operators
            # For simplicity, assuming filters match metadata structure directly for now
            # except for special keys like date_range, locations, subjects
            chroma_filters = {}
            for key, value in request.filters.items():
                 if key == "date_range" and isinstance(value, dict):
                     date_conditions = {}
                     if value.get("from"): date_conditions["$gte"] = value["from"]
                     if value.get("to"): date_conditions["$lte"] = value["to"]
                     if date_conditions: chroma_filters["date"] = date_conditions
                 elif key in ["locations", "subjects"] and isinstance(value, list) and value:
                     # Basic implementation: Check if metadata contains ANY of the provided values
                     # ChromaDB's $contains operator works on top-level string fields, not nested JSON strings directly.
                     # We store lists as JSON strings. For filtering, you might need:
                     # 1. Store tags differently (e.g., multiple entries per chunk with a single tag)
                     # 2. Perform filtering *after* retrieval (less efficient)
                     # 3. Use a DB that better supports array contains on stringified JSON (or store natively)
                     # For now, we'll skip filtering by locations/subjects in the DB query due to json.dumps
                     logger.warning(f"Filtering by '{key}' is currently not directly supported in DB query due to metadata format.")
                     pass
                 elif value: # Add other direct equality filters
                     chroma_filters[key] = value
            
            if chroma_filters:
                 where_filter = chroma_filters # Use directly if using simple equality/range
                 # If complex logic ($and, $or) is needed, construct it here
                 # where_filter = {"$and": [...]}

        logger.info(f"Querying ChromaDB with where_filter: {where_filter}")
        
        # Determine the number of results to fetch dynamically based on model context window
        n_results = request.top_k
        selected_model_id = request.model_name or model_manager.default_model_id
        model_config = model_manager.get_model_config(selected_model_id)

        if model_config:
            context_window = model_config.get("context_window", 0)
            LARGE_CONTEXT_THRESHOLD = 100000  # 100k tokens threshold for large context
            # Increase n_results significantly for large context models
            ADJUSTED_K_FOR_LARGE_CONTEXT = 200 

            if context_window >= LARGE_CONTEXT_THRESHOLD:
                # Check if user requested a low k, if so, use the adjusted high k
                if request.top_k <= 10: # Or some other threshold indicating user didn't specifically ask for many
                    n_results = ADJUSTED_K_FOR_LARGE_CONTEXT
                    logger.info(f"Model {selected_model_id} has large context ({context_window}). Adjusting retrieval to {n_results} documents as requested k ({request.top_k}) was low.")
                else:
                    # If user asked for more than 10, respect their request (up to a reasonable limit if needed)
                    n_results = request.top_k 
                    logger.info(f"Using user-requested top_k={request.top_k} for large context model {selected_model_id}.")
            else:
                # Use user's requested k or default if context isn't large
                n_results = request.top_k
                logger.info(f"Using requested/default top_k={request.top_k} for model {selected_model_id} (context: {context_window}).")
        else:
            logger.warning(f"Could not find config for model {selected_model_id}. Using requested top_k={request.top_k}.")
        
        logger.info(f"Querying ChromaDB with n_results: {n_results}")
        results = collection.query(
            query_texts=[request.query],
            n_results=n_results, # Use the determined n_results
            where=where_filter,
            # include=["metadatas", "documents", "distances"] # Include distances for relevance score
            include=["metadatas", "documents"] 
        )
        
        # Process results
        contexts = []
        sources = []
        if results and results["ids"] and results["ids"][0]:
            logger.info(f"Retrieved {len(results['ids'][0])} chunks from ChromaDB.")
            for doc, metadata, doc_id in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["ids"][0]
            ):
                # Use the full document text for the LLM context
                contexts.append(doc)  # This is the full chunk text from ChromaDB
                # Safely access metadata
                sources.append(Source(
                    id=metadata.get("article_id", doc_id), # Fallback to chunk id if article_id missing
                    title=metadata.get("title", "No Title"),
                    newspaper=metadata.get("newspaper"),
                    date=metadata.get("date"),
                    # url=metadata.get("url"), # Need to ensure URL is stored in metadata
                    text_snippet=doc[:500] + "..." if len(doc) > 500 else doc # Longer snippet (500 chars)
                ))
        else:
            logger.warning("No results found in ChromaDB for the query.")
            # Handle case with no results - return empty answer or specific message?
            query_time = (datetime.now() - start_time).total_seconds()
            return QueryResponse(
                answer="I could not find relevant information for your query.",
                sources=[],
                query_time=query_time
            )

        context_text = "\n\n---\n\n".join(contexts)
        
        # Log the context chunks being sent to the LLM for debugging
        logger.info(f"Sending {len(contexts)} context chunks to LLM for query: '{request.query}'")
        for i, ctx in enumerate(contexts):
            logger.info(f"Context chunk {i+1}: {ctx[:300]}{'...' if len(ctx) > 300 else ''}")

        # === LLM Call Logic using our new ModelManager ===
        try:
            # Note: Prompt construction is now handled inside ModelManager
            # Pass the raw query and contexts instead
            
            # Generate response using ModelManager
            answer = await model_manager.generate_response(
                user_query=request.query, 
                contexts=contexts, 
                model_id=request.model_name
            )
            logger.info(f"LLM response generated successfully.")

        except Exception as e:
            logger.error(f"Error during LLM response generation: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {e}")

        # Calculate query time
        query_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed in {query_time:.2f} seconds.")
        
        return QueryResponse(
            answer=answer or "No answer generated.", # Fallback answer
            sources=sources,
            query_time=query_time
        )
    
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error during query processing: {e}") # Log full traceback
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/filters", response_model=AvailableFilters)
def get_available_filters(collection: chromadb.Collection = Depends(get_collection)):
    logger.info("Request received for available filters.")
    try:
        # Efficiently get distinct metadata values if ChromaDB supports it directly.
        # As of now, it might require fetching a sample or all metadata.
        # Fetching a larger sample for better coverage, consider limits.
        logger.info(f"Fetching sample metadata from '{COLLECTION_NAME}' for filters...")
        results = collection.get(limit=1000, include=["metadatas"]) # Fetch more to get better stats
        
        newspapers = set()
        locations = set()
        subjects = set()
        dates = set()
        min_date: Optional[str] = None
        max_date: Optional[str] = None

        if results and results["metadatas"]:
             logger.info(f"Processing {len(results['metadatas'])} metadata records for filters.")
             for metadata in results["metadatas"]:
                if metadata:
                    if newspaper := metadata.get("newspaper"): newspapers.add(newspaper)
                    if date_str := metadata.get("date"): 
                        # Basic date validation could be added here
                        dates.add(date_str)
                        if min_date is None or date_str < min_date: min_date = date_str
                        if max_date is None or date_str > max_date: max_date = date_str

                    # Safely parse locations and subjects stored as JSON strings
                    locs = parse_json_metadata(metadata.get("locations"))
                    for loc in locs: locations.add(loc)
                    
                    subjs = parse_json_metadata(metadata.get("subjects"))
                    for subj in subjs: subjects.add(subj)
        else:
            logger.warning("No metadata found in collection to generate filters.")

        # Sort and convert to lists
        response_data = AvailableFilters(
            newspapers=sorted(list(newspapers)),
            locations=sorted(list(locations)),
            subjects=sorted(list(subjects)),
            date_range=FilterInfo(min=min_date, max=max_date)
        )
        logger.info("Filter options generated successfully.")
        return response_data
    
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(f"Error getting available filters: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving filter options: {e}")

if __name__ == "__main__":
    import uvicorn
    # Ensure ChromaDB client is initialized before starting Uvicorn if needed pre-flight
    # try:
    #     get_collection() 
    # except HTTPException as e:
    #     logger.critical(f"Failed to initialize ChromaDB connection on startup: {e.detail}")
        # Decide if server should exit or run without DB connection
        # exit(1) 
    
    logger.info("Starting Uvicorn server...")
    uvicorn.run("api:app", host="0.0.0.0", port=5000, reload=True) # Add reload=True for dev