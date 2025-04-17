import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    import tiktoken
except ImportError:
    # Handle case where tiktoken might not be installed, though it should be via requirements.txt
    logging.warning("tiktoken library not found. Token counting will be approximate.")
    tiktoken = None

# Import provider classes
from .base import LLMProvider
from .ollama_provider import OllamaProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages LLM model configurations and providers
    """
    def __init__(self, config_path: Optional[str] = None, articles_path: Optional[str] = None):
        """
        Initialize the model manager
        
        Args:
            config_path: Path to the model config JSON file
            articles_path: Path to the full articles JSON file
        """
        if config_path is None:
            # Use default path relative to this file's parent's parent (app dir)
            base_dir = Path(__file__).parent.parent
            config_path = os.path.join(base_dir, "config", "model_configs.json")

        if articles_path is None:
            # Default path for articles within the container's app dir
            base_dir = Path(__file__).parent.parent
            articles_path = os.path.join(base_dir, "data", "processed", "input_articles.json")

        self.config_path = config_path
        self.articles_path = articles_path
        self.models = {}
        self.providers = {}
        self.full_articles = {} # Dictionary to hold full article content by id

        self._initialize_providers()
        self.load_configs()
        self._load_full_articles() # Load full articles on init
        
        # Set default model from config or env
        self.default_model_id = os.getenv("MODEL_NAME", "gemma3:4b")
        logger.info(f"ModelManager initialized with default model: {self.default_model_id}")
    
    def _initialize_providers(self):
        """Initialize the provider instances"""
        self.providers = {
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        logger.info(f"Initialized providers: {', '.join(self.providers.keys())}")
    
    def load_configs(self):
        """Load model configurations from JSON file"""
        try:
            logger.info(f"Loading model configs from {self.config_path}")
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                
            for model_config in config_data.get('models', []):
                model_id = model_config.get('id')
                if model_id:
                    self.models[model_id] = model_config
                    logger.info(f"Loaded config for model: {model_id}")
                else:
                    logger.warning(f"Skipping model config without id: {model_config}")
                    
            logger.info(f"Loaded {len(self.models)} model configurations")
        except Exception as e:
            logger.error(f"Error loading model configs: {e}")
            # Initialize with empty models dictionary if loading fails
            self.models = {}
    
    def _load_full_articles(self):
        """
        Load full article content from the JSON file.
        Stores articles in a dictionary keyed by article ID.
        """
        try:
            logger.info(f"Loading full articles from {self.articles_path}")
            if not os.path.exists(self.articles_path):
                logger.error(f"Articles file not found at {self.articles_path}. Full article context will not be available.")
                self.full_articles = {}
                return

            with open(self.articles_path, 'r', encoding='utf-8') as f:
                articles_data = json.load(f)

            for article in articles_data:
                article_id = article.get('id')
                if article_id:
                    self.full_articles[article_id] = article # Store the whole article dict
                else:
                    logger.warning("Skipping article without an 'id' field.")

            logger.info(f"Loaded {len(self.full_articles)} full articles into memory.")

        except Exception as e:
            logger.error(f"Error loading full articles from {self.articles_path}: {e}")
            self.full_articles = {}
    
    def get_available_models(self) -> List[Dict[str, str]]:
        """
        Get list of available models with their ID and display name
        
        Returns:
            List of dicts with id and name for each available model
        """
        return [
            {"id": model_id, "name": config.get("name", model_id)} 
            for model_id, config in self.models.items()
        ]
    
    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific model
        
        Args:
            model_id: ID of the model
            
        Returns:
            Model configuration dict or None if not found
        """
        return self.models.get(model_id)
    
    def get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """
        Get a provider instance by name
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider instance or None if not found
        """
        return self.providers.get(provider_name)
    
    async def generate_response(self, user_query: str, retrieved_metadata: List[Dict[str, Any]], model_id: Optional[str] = None) -> str:
        """
        Generate a response using the specified model
        
        Args:
            user_query: The user's original query.
            retrieved_metadata: Metadata list from the top N retrieved chunks.
            model_id: ID of the model to use (or default if None)
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If the model or provider is not found or generation fails
        """
        # Use provided model_id or default
        model_id = model_id or self.default_model_id
        
        # Get model configuration
        model_config = self.get_model_config(model_id)
        if not model_config:
            logger.error(f"Model configuration not found for {model_id}")
            raise Exception(f"Model configuration not found: {model_id}")
        
        # Get provider name and options from config
        provider_name = model_config.get("provider")
        if not provider_name:
            logger.error(f"Provider not specified in config for model {model_id}")
            raise Exception(f"Provider not specified for model {model_id}")
        
        # Check if provider has valid API key (if needed)
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not found")
            raise Exception(f"Provider not found: {provider_name}")
        if not provider.validate_api_key():
            logger.error(f"API key validation failed for provider {provider_name}")
            raise Exception(f"API key not configured for provider {provider_name}")
        
        # Extract base options from config
        options = {
            "temperature": model_config.get("temperature", 0.3)
        }
        
        # Add model-specific options from config
        if model_config_options := model_config.get("options"):
            options.update(model_config_options)
        
        # --- NEW CONTEXT BUILDING LOGIC --- 

        # 1. Determine Tokenizer
        encoding = None
        if tiktoken:
            try:
                encoding = tiktoken.encoding_for_model(model_id)
            except KeyError:
                logger.warning(f"No specific tiktoken encoding found for {model_id}. Using cl100k_base.")
                encoding = tiktoken.get_encoding("cl100k_base")
        else:
            # Very basic fallback if tiktoken is missing
            def fallback_len(text: str) -> int:
                return len(text.split()) # Approximate with word count
            encoding = type('obj', (object,), {'encode': lambda text: text.split(), 'decode': lambda tokens: " ".join(tokens)})()
            logger.warning("Using approximate word count for tokenization.")

        # 2. Define Max Tokens and Prompt Structure
        max_model_tokens = model_config.get("context_window", 4096) # Default to smaller window if not specified
        # Estimate buffer for output tokens (adjust as needed)
        output_buffer = options.get("maxOutputTokens", options.get("max_tokens", 1024)) 
        max_prompt_tokens = max_model_tokens - output_buffer

        # Define the base prompt structure without context
        base_prompt_template = f"""Vous êtes un assistant utile pour la Collection Islam Afrique de l'Ouest (IWAC).
Votre tâche est de répondre à la question de l'utilisateur en vous basant *principalement* sur les informations contenues dans les documents de contexte suivants.
Lisez attentivement le contexte et synthétisez une réponse cohérente et analytique dans vos propres mots.
Vous pouvez synthétiser une réponse même si elle n'est pas explicitement formulée dans un seul passage, tant que les éléments sont présents dans le contexte.
Ne vous contentez pas de citer des passages du contexte, sauf si cela est essentiel pour la clarté. Si aucune information pertinente n'est trouvée dans le contexte, indiquez-le clairement.
Soyez concis dans votre réponse. Ne faites pas référence aux documents de contexte eux-mêmes dans votre réponse.

Context:
{{context_section}}

User question: {user_query}

Answer:"""

        # Calculate tokens for the base prompt (excluding the context part)
        base_prompt_tokens = len(encoding.encode(base_prompt_template.replace("{{context_section}}", "")))

        # 3. Identify Relevant Articles from Metadata
        ranked_article_ids = []
        seen_article_ids = set()
        if not self.full_articles:
             logger.warning("Full articles dictionary is empty. Cannot use full article context.")
        else:
            for meta in retrieved_metadata:
                article_id = meta.get("article_id")
                if article_id and article_id in self.full_articles and article_id not in seen_article_ids:
                    ranked_article_ids.append(article_id)
                    seen_article_ids.add(article_id)
        logger.info(f"Identified {len(ranked_article_ids)} unique relevant articles from {len(retrieved_metadata)} chunks.")

        # 4. Add Full Article Content Iteratively
        included_articles_content = []
        current_context_tokens = 0
        final_context_str = ""
        separator = "\n\n--- ARTICLE START ---\n\n"
        num_articles_included = 0

        for article_id in ranked_article_ids:
            article_data = self.full_articles.get(article_id)
            if not article_data or not article_data.get("content"):
                logger.warning(f"Skipping article {article_id}: No content found.")
                continue

            article_content = article_data["content"] # Get the full content
            article_title = article_data.get("title", "Untitled")
            article_meta_header = f"Title: {article_title}\n---\n"
            full_text_to_add = (separator + article_meta_header + article_content)
            
            # Add separator only if we already have content
            if not included_articles_content:
                 full_text_to_add = article_meta_header + article_content # No separator for the first one

            article_tokens = len(encoding.encode(full_text_to_add))

            if base_prompt_tokens + current_context_tokens + article_tokens <= max_prompt_tokens:
                included_articles_content.append(full_text_to_add)
                current_context_tokens += article_tokens
                num_articles_included += 1
            else:
                logger.warning(f"Context truncated for model {model_id}. Stopped after {num_articles_included}/{len(ranked_article_ids)} articles due to token limit ({max_prompt_tokens} prompt tokens max). Last article ({article_id}) considered was too large ({article_tokens} tokens).)")
                break # Stop adding articles if limit is reached

        final_context_str = "".join(included_articles_content)
        final_prompt = base_prompt_template.replace("{{context_section}}", final_context_str if final_context_str else "No context available.")
        final_prompt_token_count = len(encoding.encode(final_prompt))

        logger.info(f"Constructed final prompt with {num_articles_included} full articles, {final_prompt_token_count} tokens (limit: {max_prompt_tokens}).")

        # --- End NEW CONTEXT BUILDING --- 

        # Generate response
        try:
            return await provider.generate(final_prompt, model_id, options)
        except Exception as e:
            logger.error(f"Error generating response with {model_id}: {e}")
            raise

# Create a singleton instance
model_manager = ModelManager()