import os
import sys
import subprocess
import time
import chromadb
from chromadb.config import Settings

print("--- Running Check and Index Script ---")

# Configuration from Environment Variables
chroma_host = os.getenv("CHROMADB_HOST", "chromadb")
chroma_port = int(os.getenv("CHROMADB_PORT", 8000))
collection_name = os.getenv("COLLECTION_NAME", "iwac_articles") # Ensure this matches your .env or default
input_json_path_default = "/app/data/processed/input_articles.json" 
# Allow overriding input path via script argument if needed in the future
input_json_path = sys.argv[1] if len(sys.argv) > 1 else input_json_path_default

print(f"ChromaDB Host: {chroma_host}")
print(f"ChromaDB Port: {chroma_port}")
print(f"Collection Name: {collection_name}")
print(f"Input JSON Path: {input_json_path}")

# Check if input file exists
if not os.path.exists(input_json_path):
    print(f"ERROR: Input JSON file not found at {input_json_path}. Skipping indexing check.", file=sys.stderr)
    # Exit cleanly if no input file, as indexing cannot proceed.
    # The main application might still run, depending on requirements.
    sys.exit(0) 

# --- Wait for ChromaDB ---
# Although docker-compose depends_on helps, add a small explicit wait/retry
max_retries = 10
retry_delay = 5 # seconds
for i in range(max_retries):
    try:
        # Test connection - List collections is a lightweight operation
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port, settings=Settings(allow_reset=True))
        client.list_collections()
        print("Successfully connected to ChromaDB.")
        break 
    except Exception as e:
        print(f"Waiting for ChromaDB ({i+1}/{max_retries})... Error: {e}")
        if i == max_retries - 1:
            print("ERROR: Could not connect to ChromaDB after multiple retries. Exiting.", file=sys.stderr)
            sys.exit(1) # Exit with error if ChromaDB connection fails
        time.sleep(retry_delay)

# --- Check Collection ---
needs_indexing = False
try:
    # Use get_or_create_collection to ensure the collection exists
    collection = client.get_or_create_collection(name=collection_name)
    print(f"Ensured collection '{collection_name}' exists.")
    
    # Now check the count
    count = collection.count()
    print(f"Collection '{collection_name}' contains {count} documents.")
    if count == 0:
        print("Collection is empty. Indexing required.")
        needs_indexing = True
    else:
        print("Collection already contains data. Skipping indexing.")
except Exception as e:
    print(f"ERROR: Failed during collection check/creation: {e}", file=sys.stderr)
    # Exit if we can't even ensure the collection exists or check its count
    sys.exit(1) 

# --- Run Indexing Script if Needed ---
if needs_indexing:
    print(f"Starting indexing from {input_json_path}...")
    indexing_script_path = "/app/scripts/index_to_chroma.py"
    command = [
        "python", 
        indexing_script_path,
        "--input", input_json_path,
        "--chroma-host", chroma_host,
        "--chroma-port", str(chroma_port),
        "--collection", collection_name
        # Add other necessary arguments for index_to_chroma.py if any
    ]
    
    try:
        # Use subprocess.run to execute the script
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Indexing script completed successfully.")
        print("--- Indexing Script STDOUT ---")
        print(result.stdout)
        print("-----------------------------")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Indexing script failed with exit code {e.returncode}.", file=sys.stderr)
        print("--- Indexing Script STDOUT --- DUMP:", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("--- Indexing Script STDERR --- DUMP:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        print("-----------------------------------", file=sys.stderr)
        sys.exit(1) # Exit with error if indexing fails
    except FileNotFoundError:
        print(f"ERROR: Indexing script not found at {indexing_script_path}", file=sys.stderr)
        sys.exit(1)
else:
    print("Skipping indexing process.")

print("--- Check and Index Script Finished ---")
sys.exit(0) # Ensure exiting with 0 if successful 