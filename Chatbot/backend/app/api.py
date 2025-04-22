import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# === Moved Logging Configuration START ===
# Basic logging configuration - Place this EARLY
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# === Moved Logging Configuration END ===

# Load environment variables from the project root .env file - Place this AFTER logging setup
load_dotenv(Path(__file__).parents[2] / '.env')

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
import requests
import json
import re # Import regex module

# Import our new ModelManager - Keep this AFTER logging setup
from app.models import model_manager

# No longer needed here:
# Basic logging configuration
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# Added import for datetime which was potentially removed above? Ensure it's present.
from datetime import datetime

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
    prompt_token_count: Optional[int] = None # Add field for token count
    answer_token_count: Optional[int] = None # Add field for answer token count

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

        logger.info(f"Constructed ChromaDB where_filter: {where_filter}")
        
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
        
        logger.info(f"Starting ChromaDB query with n_results: {n_results}...")
        results = collection.query(
            query_texts=[request.query],
            n_results=n_results, # Use the determined n_results
            where=where_filter,
            # include=["metadatas", "documents", "distances"] # Include distances for relevance score
            include=["metadatas", "documents"] 
        )
        logger.info(f"ChromaDB query completed. Retrieved {len(results['ids'][0]) if results and results['ids'] else 0} chunks.")
        
        # Process results - NOW focusing on getting unique relevant article IDs
        # contexts = [] # No longer collecting chunk text here
        sources = [] # Still collect source snippets for display
        retrieved_metadata = [] # Collect metadata from retrieved chunks

        if results and results["ids"] and results["ids"][0]:
            # logger.info(f"Retrieved {len(results['ids'][0])} chunks from ChromaDB.") # Already logged above
            for doc_text, metadata, doc_id in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["ids"][0]
            ):
                # Store metadata for context building later
                retrieved_metadata.append(metadata)

                # Use the chunk document text for the source snippet
                sources.append(Source(
                    id=metadata.get("article_id", doc_id), # Fallback to chunk id if article_id missing
                    title=metadata.get("title", "No Title"),
                    newspaper=metadata.get("newspaper"),
                    date=metadata.get("date"),
                    # url=metadata.get("url"), # Reverted: No need for external URL
                    text_snippet=doc_text[:500] + "..." if len(doc_text) > 500 else doc_text # Snippet from chunk
                ))
        else:
            logger.warning("No results found in ChromaDB for the query.")
            # Handle case with no results - return empty answer or specific message?
            query_time = (datetime.now() - start_time).total_seconds()
            return QueryResponse(
                answer="I could not find relevant information for your query.",
                sources=[],
                query_time=query_time,
                prompt_token_count=None,
                answer_token_count=None
            )

        # context_text = "\n\n---\n\n".join(contexts) # Removed - context built differently now
        
        # Log the *metadata* being sent to the LLM for debugging
        # logger.info(f"Sending {len(contexts)} context chunks to LLM for query: '{request.query}'")
        # for i, ctx in enumerate(contexts):
        #     logger.info(f"Context chunk {i+1}: {ctx[:300]}{'...' if len(ctx) > 300 else ''}")
        logger.info(f"Preparing LLM request. Passing metadata for {len(retrieved_metadata)} retrieved chunks to ModelManager for query: '{request.query}'")

        # === LLM Call Logic using our new ModelManager ===
        try:
            # Note: Prompt construction is now handled inside ModelManager
            # Pass the raw query and RETRIEVED METADATA instead of chunk text
            
            logger.info(f"Calling ModelManager.generate_response with model '{request.model_name or model_manager.default_model_id}'...")
            # Generate response using ModelManager - unpack token counts
            answer, used_article_ids, prompt_tokens, answer_tokens = await model_manager.generate_response(
                user_query=request.query,
                retrieved_metadata=retrieved_metadata,
                model_id=request.model_name
            )
            logger.info(f"LLM response generated successfully by ModelManager.")
            logger.info(f"Actual articles used for context: {used_article_ids}")
            logger.info(f"Prompt token count: {prompt_tokens}") # Log the token count
            logger.info(f"Answer token count: {answer_tokens}") # Log the token count

            # Filter sources to include only those whose articles were actually used
            final_sources = []
            added_source_ids = set()
            if used_article_ids:
                for source in sources: # Iterate through original sources (derived from chunks)
                    # Use the article_id from the source object
                    article_id = source.id # Assuming source.id holds the article_id
                    if article_id in used_article_ids and article_id not in added_source_ids:
                        final_sources.append(source)
                        added_source_ids.add(article_id)
            else:
                logger.warning("No specific article IDs were reported as used for context.")
                # Optionally decide what to show if no articles were used - maybe none?
                # Or show the original top sources as a fallback?
                # For now, let's return an empty list if used_article_ids is empty
                final_sources = []

        except Exception as e:
            logger.error(f"Error during LLM response generation via ModelManager: {e}")
            raise HTTPException(status_code=500, detail=f"Error generating response: {e}")

        # Calculate query time
        query_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed successfully in {query_time:.2f} seconds.")
        
        return QueryResponse(
            answer=answer or "No answer generated.", # Fallback answer
            sources=final_sources,
            query_time=query_time,
            prompt_token_count=prompt_tokens, # Include token count in response
            answer_token_count=answer_tokens # Include answer token count in response
        )
    
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        logger.exception(f"Unexpected error during query processing: {e}") # Log full traceback
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/filters", response_model=AvailableFilters)
def get_available_filters(collection: chromadb.Collection = Depends(get_collection)):
    """
    Get available filter options from the metadata in the ChromaDB collection
    """
    try:
        # Log the current number of documents in the collection
        count = collection.count()
        logger.info(f"Fetching filters. Collection '{collection.name}' currently contains {count} documents.")

        # Retrieve a sample of metadata to determine available filters
        # Note: collection.get() without IDs/where might be inefficient for large collections
        # Consider optimizing if performance becomes an issue (e.g., dedicated metadata store or sampling)
        # Fetching *all* metadata might be too slow/memory intensive
        # Let's fetch a reasonable number of documents to get a representative sample
        metadata_sample = collection.get(limit=20000, include=["metadatas"]) # Increase limit to cover all documents

        if not metadata_sample or not metadata_sample.get("metadatas"):
            logger.warning("No metadata found in collection to generate filters.")
            # Return empty filters if collection is empty or has no metadata
            return AvailableFilters(
                newspapers=[],
                locations=[],
                subjects=[],
                date_range=FilterInfo(min=None, max=None)
            )
        
        # Use sets for efficient collection of unique values
        newspapers = set()
        locations = set()
        subjects = set()
        dates = []

        # --- Remove DEBUG LOGGING --- 
        # raw_newspapers_found = [] 
        # --- END DEBUG --- 

        invalid_date_formats_found = set() # To log unique invalid formats

        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$") # Regex for YYYY-MM-DD

        for meta in metadata_sample["metadatas"]:
            if meta:
                newspaper_name = meta.get("newspaper")
                if newspaper_name:
                    newspapers.add(newspaper_name)
                    # raw_newspapers_found.append(newspaper_name) # Removed debug line
                
                date_str = meta.get("date")
                if date_str: # Check if date exists
                    if date_pattern.match(date_str): # Check if it matches YYYY-MM-DD
                        dates.append(date_str)
                    else:
                        invalid_date_formats_found.add(str(date_str)) # Log invalid format found

                # Safely parse JSON string lists for locations and subjects
                loc_list = parse_json_metadata(meta.get("locations"))
                subj_list = parse_json_metadata(meta.get("subjects"))
                locations.update(loc_list)
                subjects.update(subj_list)

        # Determine min/max dates
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None

        # Sort lists for consistent frontend display
        sorted_newspapers = sorted(list(newspapers))
        sorted_locations = sorted(list(locations))
        sorted_subjects = sorted(list(subjects))

        # --- Remove DEBUG LOGGING --- 
        # logger.info(f"DEBUG: Raw newspapers found in sample: {raw_newspapers_found}")
        # --- END DEBUG --- 

        # Log if any invalid date formats were skipped
        if invalid_date_formats_found:
            logger.warning(f"Skipped the following non 'YYYY-MM-DD' date formats found in metadata: {list(invalid_date_formats_found)}")

        logger.info(f"Returning {len(sorted_newspapers)} newspapers, {len(sorted_locations)} locations, {len(sorted_subjects)} subjects.")
        logger.info(f"Date range derived from valid dates: {min_date} to {max_date}")

        return AvailableFilters(
            newspapers=sorted_newspapers,
            locations=sorted_locations,
            subjects=sorted_subjects,
            date_range=FilterInfo(min=min_date, max=max_date)
        )

    except Exception as e:
        logger.error(f"Error retrieving filters: {e}", exc_info=True) # Log traceback
        raise HTTPException(status_code=500, detail=f"Failed to retrieve filters: {str(e)}")

# === Check and Index on Startup (Optional) ===
# Simple check: Does the collection exist and have documents?
# Note: This runs in the main process, potentially blocking startup.
# Consider a background task or separate management command for production.

if __name__ == "__main__":
    # This block is for running directly with uvicorn, not Docker typically
    # For Docker, entrypoint/CMD handles startup
    logger.info("Starting API server with Uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=5000) # Use port 5000 for consistency
    # Consider adding reload=True for local development only
    # uvicorn.run("app.api:app", host="0.0.0.0", port=5000, reload=True)