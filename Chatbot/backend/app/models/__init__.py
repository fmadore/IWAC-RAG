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

logger = logging.getLogger(__name__)

class ModelManager:
    """
    Manages LLM model configurations and providers
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model manager
        
        Args:
            config_path: Path to the model config JSON file
        """
        if config_path is None:
            # Use default path relative to this file
            base_dir = Path(__file__).parent.parent
            config_path = os.path.join(base_dir, "config", "model_configs.json")
        
        self.config_path = config_path
        self.models = {}
        self.providers = {}
        self._initialize_providers()
        self.load_configs()
        
        # Set default model from config or env
        self.default_model_id = os.getenv("MODEL_NAME", "gemma3:4b")
        logger.info(f"ModelManager initialized with default model: {self.default_model_id}")
    
    def _initialize_providers(self):
        """Initialize the provider instances"""
        self.providers = {
            "ollama": OllamaProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider()
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
    
    async def generate_response(self, user_query: str, contexts: List[str], model_id: Optional[str] = None) -> str:
        """
        Generate a response using the specified model
        
        Args:
            user_query: The user's original query.
            contexts: A list of context documents retrieved from the database.
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
        if not self.get_provider(provider_name).validate_api_key():
            logger.error(f"API key validation failed for provider {provider_name}")
            raise Exception(f"API key not configured for provider {provider_name}")
        
        # Extract options from config
        options = {
            "temperature": model_config.get("temperature", 0.3)
        }
        
        # Add model-specific options from config
        if model_config_options := model_config.get("options"):
            options.update(model_config_options)
        
        # --- Token Counting and Prompt Construction --- 

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
        output_buffer = model_config.get("options", {}).get("maxOutputTokens", 1024) 
        max_prompt_tokens = max_model_tokens - output_buffer

        # Define the base prompt structure without context
        base_prompt_template = f"""Vous êtes un assistant utile pour la Collection Islam Afrique de l'Ouest (IWAC).
Votre tâche est de répondre à la question de l'utilisateur en vous basant *uniquement* sur les informations contenues dans les documents de contexte suivants.
Lisez attentivement le contexte et synthétisez une réponse cohérente et analytique dans vos propres mots.
Ne vous contentez pas de citer des passages du contexte, sauf si cela est essentiel pour la clarté. Si les informations nécessaires pour répondre à la question ne sont pas présentes dans le contexte, indiquez-le clairement.
Soyez concis dans votre réponse. Ne faites pas référence aux documents de contexte eux-mêmes dans votre réponse.

Context:
{{context_section}}

User question: {user_query}

Answer:"""

        # Calculate tokens for the base prompt (excluding the context part)
        base_prompt_tokens = len(encoding.encode(base_prompt_template.replace("{{context_section}}", "")))

        # 3. Add Context Documents Iteratively
        included_contexts = []
        current_context_tokens = 0
        final_context_str = ""
        separator = "\n\n---\n\n"

        for doc in contexts:
            doc_with_separator = separator + doc if included_contexts else doc # Add separator before docs > 0
            doc_tokens = len(encoding.encode(doc_with_separator))

            if base_prompt_tokens + current_context_tokens + doc_tokens <= max_prompt_tokens:
                included_contexts.append(doc_with_separator)
                current_context_tokens += doc_tokens
            else:
                logger.warning(f"Context truncated for model {model_id}. Stopped after {len(included_contexts)}/{len(contexts)} documents due to token limit ({max_prompt_tokens} prompt tokens max).")
                break # Stop adding documents if limit is reached

        final_context_str = "".join(included_contexts)
        final_prompt = base_prompt_template.replace("{{context_section}}", final_context_str if final_context_str else "No context available.")
        final_prompt_token_count = len(encoding.encode(final_prompt))

        logger.info(f"Constructed final prompt with {len(included_contexts)} documents, {final_prompt_token_count} tokens (limit: {max_prompt_tokens}).")

        # --- End Token Counting --- 

        # Get provider instance
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not found")
            raise Exception(f"Provider not found: {provider_name}")
        
        # Generate response
        try:
            return await provider.generate(final_prompt, model_id, options)
        except Exception as e:
            logger.error(f"Error generating response with {model_id}: {e}")
            raise

# Create a singleton instance
model_manager = ModelManager()