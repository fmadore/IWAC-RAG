import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
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
            base_dir = Path(__file__).parent.parent # /app/app
            config_path = os.path.join(base_dir, "config", "model_configs.json") # /app/app/config/... OK

        if articles_path is None:
            # Default path for articles within the container's app dir
            # The volume maps to /app/data, not /app/app/data
            # Go up one more level from base_dir (/app/app) to get to /app
            app_root_dir = Path(__file__).parent.parent.parent # /app
            articles_path = os.path.join(app_root_dir, "data", "processed", "input_articles.json") # /app/data/processed/... Correct!

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
    
    async def generate_response(self, user_query: str, retrieved_metadata: List[Dict[str, Any]], model_id: Optional[str] = None) -> Tuple[str, List[str], int, int]:
        """
        Generate a response using the specified model and return the answer, used article IDs, prompt token count, and answer token count.

        Args:
            user_query: The user's original query.
            retrieved_metadata: Metadata list from the top N retrieved chunks.
            model_id: ID of the model to use (or default if None)

        Returns:
            A tuple containing:
                - The generated response text (str)
                - A list of article IDs actually used in the context (List[str])
                - The total number of tokens in the final prompt sent to the LLM (int)
                - The total number of tokens in the generated answer (int)

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
        
        # Get provider instance
        provider = self.get_provider(provider_name)
        if not provider:
            logger.error(f"Provider {provider_name} not found")
            raise Exception(f"Provider not found: {provider_name}")
        if not provider.validate_api_key(): # Validate API key early
            logger.error(f"API key validation failed for provider {provider_name}")
            raise Exception(f"API key not configured for provider {provider_name}")

        # Initialize token counting specific variables
        encoding = None
        # --- Removed Gemini-specific model instance initialization --- 
        # gemini_model_instance = None
        # if provider_name == "gemini":
        #     try:
        #         full_model_id = f"models/{model_id}" if not model_id.startswith("models/") else model_id
        #         gemini_model_instance = genai.GenerativeModel(full_model_id)
        #     except Exception as e:
        #         logger.error(f"Failed to initialize Gemini model {model_id} for token counting: {e}")
        #         raise Exception(f"Failed to initialize Gemini model {model_id} for token counting: {e}")
        
        # Setup tiktoken encoding if not using Gemini (or as fallback)
        if provider_name != "gemini" and tiktoken:
            try:
                encoding = tiktoken.encoding_for_model(model_id)
            except KeyError:
                logger.warning(f"No specific tiktoken encoding for {model_id}. Using cl100k_base.")
                encoding = tiktoken.get_encoding("cl100k_base")
        elif provider_name != "gemini":
            logger.warning("tiktoken not available. Using approximate word count for non-Gemini models.")
            # Basic fallback for non-gemini
            encoding = type('obj', (object,), {'encode': lambda text: text.split()})()

        # Define token counting function based on provider
        # NOTE: This function is now synchronous
        def count_tokens_func(text_to_count: str) -> int:
            # --- Use the new SDK client for Gemini token counting --- 
            if provider_name == "gemini":
                try:
                    # Get the initialized client from the provider instance
                    gemini_provider = self.get_provider("gemini")
                    if gemini_provider and gemini_provider.client:
                        # Construct model name, ensure models/ prefix
                        full_model_id_for_count = f"models/{model_id}" if not model_id.startswith("models/") else model_id
                        # Call the client's count_tokens method (assuming it exists and is sync)
                        count_response = gemini_provider.client.models.count_tokens(
                            model=full_model_id_for_count,
                            contents=text_to_count
                        )
                        return count_response.total_tokens
                    else:
                        logger.error("Gemini provider or client not initialized for token counting. Falling back.")
                        return len(text_to_count.split()) # Fallback
                except Exception as e:
                    logger.error(f"Gemini count_tokens (google-genai SDK) failed: {e}. Falling back to approx.")
                    return len(text_to_count.split()) # Fallback
            elif encoding: # Use tiktoken for other providers if available
                return len(encoding.encode(text_to_count))
            else: # Absolute fallback (word count)
                 return len(text_to_count.split())

        # --- Context Building & Token Calculation --- 
        
        # Extract base options from config
        options = {
            "temperature": model_config.get("temperature", 0.3)
        }
        if model_config_options := model_config.get("options"):
            options.update(model_config_options)

        # Define Max Tokens (remains the same logic)
        max_model_tokens = model_config.get("context_window", 4096)
        output_buffer = options.get("maxOutputTokens", options.get("max_tokens", 1024)) 
        max_prompt_tokens = max_model_tokens - output_buffer

        # Use the new prompt provided by the user (v4 - Max Output Tokens)
        base_prompt_template = ("""
Vous êtes IWAC Chat Explorer, un analyste expert spécialisé dans l'interprétation critique des documents de la Collection Islam Afrique de l'Ouest (IWAC). Votre expertise est d'offrir une analyse approfondie basée exclusivement sur les documents fournis.

Instructions fondamentales:

1. ANALYSE CRITIQUE APPROFONDIE: Allez au-delà de la simple présentation des faits. Analysez les tendances, les dynamiques de pouvoir, les évolutions historiques, et les implications socio-politiques des événements décrits dans les documents.

2. ANCRAGE DANS DES ÉVÉNEMENTS CONCRETS: Appuyez votre analyse sur des événements, personnes et dates spécifiques mentionnés dans les documents. Référez-vous à "la conférence de l'Union musulmane du Togo en octobre 1997" ou "la déclaration du président Eyadéma lors de la rencontre avec les leaders religieux", plutôt qu'à "un article" ou "une source".

3. CONTEXTUALISATION ET INTERPRÉTATION: Replacez les événements dans leur contexte politique, social ou religieux tel que révélé par les documents. Interprétez ce que ces événements révèlent sur les dynamiques religieuses, les relations État-religion, ou les tendances sociales.

4. ANALYSE DES TRANSFORMATIONS: Identifiez et analysez les continuités et ruptures dans les phénomènes décrits. Comment les situations, attitudes ou politiques ont-elles évolué au fil du temps selon les documents?

5. DÉCRYPTAGE DES ENJEUX: Identifiez les enjeux sous-jacents aux événements décrits - luttes d'influence, négociations de pouvoir, questions identitaires ou autres dimensions que les documents permettent de percevoir.

6. LECTURE CRITIQUE: Analysez comment les événements sont présentés dans les documents. Quels aspects sont mis en avant? Quelles perspectives semblent privilégiées? Quels silences ou omissions peut-on constater?

7. PRUDENCE MÉTHODOLOGIQUE: Distinguez clairement entre les faits établis et vos interprétations. Signalez les limites des documents pour répondre à certains aspects de la question.

8. ORGANISATION ANALYTIQUE: Structurez votre réponse autour de thèmes analytiques ou d'une progression chronologique qui fait ressortir les évolutions significatives.

Ne citez pas directement les sources, mais démontrez votre compréhension approfondie en analysant leur contenu de manière rigoureuse et nuancée, tout en restant exclusivement dans les limites des informations présentes dans les documents fournis.

Context:
{{context_section}}

User question: {user_query}

Answer:
""")
        # Calculate base prompt tokens using the appropriate method
        # Need to call the sync function directly
        base_prompt_for_calc = base_prompt_template.format(context_section="placeholder", user_query="placeholder")
        base_prompt_tokens = count_tokens_func(base_prompt_for_calc)

        # Identify Relevant Articles (remains the same logic)
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

        # Add Full Article Content Iteratively using accurate token counts
        included_articles_content = []
        used_article_ids = []
        current_context_tokens = 0
        separator = "\n\n--- ARTICLE START ---\n\n"
        num_articles_included = 0

        for article_id in ranked_article_ids:
            article_data = self.full_articles.get(article_id)
            if not article_data or not article_data.get("content"):
                logger.warning(f"Skipping article {article_id}: No content found.")
                continue

            article_content = article_data["content"] 
            article_title = article_data.get("title", "Untitled")
            article_meta_header = f"Title: {article_title}\n---\n"
            # Construct text to add *for token calculation*
            text_to_add_for_calc = (separator + article_meta_header + article_content) if included_articles_content else (article_meta_header + article_content)

            # Calculate article tokens using the appropriate method (sync call)
            article_tokens = count_tokens_func(text_to_add_for_calc)

            # --- DEBUG LOG START ---
            logger.debug(f"Article {article_id}: Content length={len(article_content)}, Calculated tokens={article_tokens}, Cumulative tokens={current_context_tokens + article_tokens}")
            # --- DEBUG LOG END ---

            if base_prompt_tokens + current_context_tokens + article_tokens <= max_prompt_tokens:
                # If it fits, add the actual content (with separator if needed)
                actual_text_to_append = (separator + article_meta_header + article_content) if included_articles_content else (article_meta_header + article_content)
                included_articles_content.append(actual_text_to_append)
                current_context_tokens += article_tokens # Add the calculated tokens
                num_articles_included += 1
                used_article_ids.append(article_id)
            else:
                logger.warning(f"Context truncated for model {model_id}. Stopped after {num_articles_included}/{len(ranked_article_ids)} articles due to token limit ({max_prompt_tokens} prompt tokens max). Last article ({article_id}) considered required {article_tokens} tokens.)")
                break

        final_context_str = "".join(included_articles_content)
        final_prompt = base_prompt_template.format(
            context_section=final_context_str if final_context_str else "No context available.",
            user_query=user_query
        )
        
        # Calculate final prompt tokens accurately (sync call)
        # !!! BUG FIX: Use the sum of tokens calculated during context building, 
        #     don't recalculate on the potentially huge final_prompt string !!!
        # final_prompt_token_count = count_tokens_func(final_prompt) # Old buggy way
        final_prompt_token_count = base_prompt_tokens + current_context_tokens # Correct way
        logger.info(f"Constructed final prompt with {num_articles_included} full articles (IDs: {used_article_ids}), calculated {final_prompt_token_count} tokens (limit: {max_prompt_tokens}).")

        # --- Generate response using the chosen provider --- 
        try:
            # The provider.generate method only needs the final prompt, model_id, and options
            answer = await provider.generate(final_prompt, model_id, options)
            
            # Calculate answer token count accurately (sync call)
            answer_token_count = count_tokens_func(answer)
            logger.info(f"Calculated answer token count: {answer_token_count}")

            # Return answer, used IDs, and both token counts
            return answer, used_article_ids, final_prompt_token_count, answer_token_count 
        except Exception as e:
            logger.error(f"Error generating response with {model_id}: {e}")
            raise

# Create a singleton instance
model_manager = ModelManager()