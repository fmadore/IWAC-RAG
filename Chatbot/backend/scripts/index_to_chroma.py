import json
import chromadb
import argparse
import nltk
from chromadb.utils import embedding_functions
from tqdm import tqdm
from typing import List, Dict, Any

# Download necessary NLTK resources for English (default) and French
try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')
try:
    nltk.data.find('tokenizers/punkt/french.pickle')
except nltk.downloader.DownloadError:
    # punkt contains multiple languages, including French
    # If the above fails, redownloading punkt might be needed
    # Or specifically download french part if possible
    print("Downloading NLTK punkt data (includes French)...")
    nltk.download('punkt')

def process_article(article: Dict[str, Any], chunk_size: int = 512, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    Process an article into chunks suitable for embedding, using the provided JSON structure.
    Maps 'subject' -> 'subjects' and 'spatial' -> 'locations'.
    """
    content = article.get("content", "")
    if not content:
        return []
    
    # Pre-process content to handle different newline/paragraph break styles
    content = content.replace('\\r\\n\\r\\n', ' ') # Replace double carriage return/newline
    content = content.replace('\\n\\n', ' ')     # Replace double newline
    content = content.replace('\\r\\n', ' ')    # Replace single carriage return/newline
    content = content.replace('\\n', ' ')       # Replace single newline just in case
    
    # Use NLTK to split into sentences, specifying French
    try:
        sentences = nltk.sent_tokenize(content, language='french')
    except Exception as e:
        print(f"Error tokenizing article {article.get('id', '')}: {e}. Falling back to default tokenization.")
        # Fallback to default if French data isn't loaded or causes error
        sentences = nltk.sent_tokenize(content)
    
    chunks = []
    current_chunk = ""
    current_chunk_sentences = []
    
    # Extract metadata, handling potential missing keys gracefully
    article_id = article.get("id", "")
    title = article.get("title", "")
    newspaper = article.get("newspaper", "")
    # Ensure date is treated as a string
    date = str(article.get("date", "")) 
    # Map subject/spatial keywords to subjects/locations lists
    subjects_keywords = article.get("subject", [])
    if isinstance(subjects_keywords, str): # Handle if it's a single string
        subjects_keywords = [subjects_keywords]
        
    locations_keywords = article.get("spatial", [])
    if isinstance(locations_keywords, str): # Handle if it's a single string
        locations_keywords = [locations_keywords]

    for sentence in sentences:
        # If adding this sentence would exceed chunk size and we already have content
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            # Create chunk document
            chunk_doc = {
                "id": f"{article_id}_chunk_{len(chunks)}",
                "article_id": article_id,
                "text": current_chunk.strip(), # Strip leading/trailing whitespace
                "title": title,
                "newspaper": newspaper,
                "date": date,
                "subjects": subjects_keywords, # Use the mapped list
                "locations": locations_keywords, # Use the mapped list
                "chunk_idx": len(chunks),
            }
            chunks.append(chunk_doc)
            
            # Start new chunk with overlap using sentences
            overlap_sentences = current_chunk_sentences[-3:] 
            overlap_text = " ".join(overlap_sentences)
            
            if len(overlap_text) < chunk_size: 
                current_chunk = overlap_text + " " + sentence
                current_chunk_sentences = overlap_sentences + [sentence]
            else:
                current_chunk = sentence
                current_chunk_sentences = [sentence]

        else:
            # Add sentence to current chunk
            current_chunk += (" " + sentence) if current_chunk else sentence
            current_chunk_sentences.append(sentence)
    
    # Add the last chunk if it has content
    if current_chunk:
        chunk_doc = {
            "id": f"{article_id}_chunk_{len(chunks)}",
            "article_id": article_id,
            "text": current_chunk.strip(), # Strip leading/trailing whitespace
            "title": title,
            "newspaper": newspaper,
            "date": date,
            "subjects": subjects_keywords, # Use the mapped list
            "locations": locations_keywords, # Use the mapped list
            "chunk_idx": len(chunks),
        }
        chunks.append(chunk_doc)
    
    return chunks

def index_articles(input_file: str, chroma_host: str, chroma_port: int, collection_name: str, chunk_size: int, overlap: int) -> None:
    """
    Index articles into ChromaDB
    """
    client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    
    # Use a multilingual model for embedding
    # model_name = "all-MiniLM-L6-v2" # Old model
    model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    print(f"Using embedding model: {model_name}")
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=model_name
    )
    
    # Create or get collection
    try:
        collection = client.get_collection(name=collection_name, embedding_function=embedding_function)
        print(f"Using existing collection: {collection_name}")
    except Exception as e:
        print(f"Collection not found, creating new one: {e}")
        collection = client.create_collection(name=collection_name, embedding_function=embedding_function)
        print(f"Created new collection: {collection_name}")
    
    with open(input_file, "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    all_chunks = []
    for article in tqdm(articles, desc="Processing articles"):
        chunks = process_article(article, chunk_size, overlap)
        all_chunks.extend(chunks)
    
    # Add documents in batches
    batch_size = 100
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Indexing chunks"):
        batch = all_chunks[i:i+batch_size]
        
        ids = [chunk["id"] for chunk in batch]
        texts = [chunk["text"] for chunk in batch]
        metadatas = [{
            "article_id": chunk["article_id"],
            "title": chunk["title"],
            "newspaper": chunk["newspaper"],
            "date": chunk["date"],
            # Ensure subjects/locations are dumped as JSON strings for ChromaDB metadata
            "subjects": json.dumps(chunk.get("subjects", [])), 
            "locations": json.dumps(chunk.get("locations", [])),
            "chunk_idx": chunk["chunk_idx"]
        } for chunk in batch]
        
        try:
            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
        except Exception as e:
             print(f"Error adding batch {i//batch_size}: {e}")
             # Optional: Add more robust error handling, e.g., retries or logging failed IDs

    print(f"Indexed {len(all_chunks)} chunks from {len(articles)} articles into ChromaDB collection '{collection_name}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index articles from a JSON file into ChromaDB")
    parser.add_argument("--input", default="../../data/processed/input_articles.json", help="Input JSON file path")
    parser.add_argument("--chroma-host", default="localhost", help="ChromaDB host")
    parser.add_argument("--chroma-port", type=int, default=8000, help="ChromaDB port")
    parser.add_argument("--collection", default="iwac_articles", help="ChromaDB collection name")
    parser.add_argument("--chunk-size", type=int, default=512, help="Chunk size in characters")
    parser.add_argument("--overlap", type=int, default=100, help="Overlap size in characters (used for sentence context)")
    
    args = parser.parse_args()
    
    index_articles(args.input, args.chroma_host, args.chroma_port, args.collection, args.chunk_size, args.overlap) 