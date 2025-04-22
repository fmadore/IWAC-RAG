import os
import logging
from typing import Dict, Any
from .base import LLMProvider
# Updated imports for the new SDK
from google import genai
from google.genai import types 
from google.genai import errors

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    Implementation of LLMProvider for Google's Gemini API using the google-genai SDK.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None # Initialize client to None
        if self.api_key:
            try:
                # Initialize the client directly using the new SDK style
                self.client = genai.Client(api_key=self.api_key)
                # Simple check: Try listing models to validate connection/key
                # Note: This might be slow or incur a small cost, alternative is just relying on the first generate call to fail
                # For simplicity, let's assume client initialization is enough, 
                # or rely on the first generate call failing if key is bad.
                # models_list = list(self.client.models.list()) # Example check
                # if not models_list:
                #    raise Exception("Failed to list models. API key might be invalid or no models accessible.")
                logger.info("GeminiProvider initialized successfully with google-genai Client.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client (google-genai): {e}")
                self.client = None # Ensure client is None if init fails
        else:
            logger.warning("GEMINI_API_KEY not found in environment.")
            # self.api_key is already None if not found

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using the google-genai SDK.
        """
        if not self.validate_api_key():
            raise Exception("Gemini Client not initialized. Check API key and initial setup.")

        logger.info(f"Generating response with Gemini model: {model_id} using google-genai SDK")

        try:
            # Model ID for the new SDK usually doesn't need the 'models/' prefix for generate_content
            # However, the client handles variations, so let's keep it simple.
            # If issues arise, we might need model = client.models.get(f'models/{model_id}') first.
            
            # Prepare generation config using types.GenerateContentConfig
            gen_config_dict = {
                "temperature": options.get("temperature", 0.3),
            }
            # The new SDK uses 'max_output_tokens' directly within GenerateContentConfig
            max_tokens = options.get("maxOutputTokens") 
            if max_tokens is not None:
                gen_config_dict["max_output_tokens"] = int(max_tokens)

            if options.get("topP") is not None:
                 gen_config_dict["top_p"] = options.get("topP")
            if options.get("topK") is not None:
                 gen_config_dict["top_k"] = options.get("topK")
            stop_sequences = options.get("stopSequences")
            if stop_sequences and isinstance(stop_sequences, list):
                gen_config_dict["stop_sequences"] = stop_sequences

            # Prepare thinking config if budget is specified
            thinking_config = None # Initialize thinking_config to None
            thinking_budget = options.get("thinkingBudget")
            if thinking_budget is not None:
                try:
                    thinking_config = types.ThinkingConfig(
                        thinking_budget=int(thinking_budget)
                    )
                    logger.info(f"Using thinking budget: {thinking_budget}")
                except ValueError:
                    logger.warning(f"Invalid thinkingBudget value: {thinking_budget}. Ignoring.")
                except AttributeError:
                    logger.warning("ThinkingConfig attribute not found unexpectedly. Skipping.")

            # Create the config object, including thinking_config if specified
            if thinking_config is not None:
                gen_config_dict["thinking_config"] = thinking_config
            generation_config = types.GenerateContentConfig(**gen_config_dict)

            # Ensure model ID has 'models/' prefix
            full_model_id = f'models/{model_id}' if not model_id.startswith("models/") else model_id

            # Generate content using async client
            response = await self.client.aio.models.generate_content(
                model=full_model_id,
                contents=prompt,
                config=generation_config
            )
            
            # --- Extract the text response using the new simpler way --- 
            # Need to handle potential blocking reasons first
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason
                block_details = ""
                if hasattr(response.prompt_feedback, 'safety_ratings'):
                    block_details = f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
                logger.error(f"Gemini request blocked. Reason: {block_reason}.{block_details}")
                raise Exception(f"Content blocked by Gemini API due to: {block_reason}.{block_details}")
            
            # Check if response has text (might not if blocked or other issues)
            # The new SDK might raise an exception directly for some errors
            try:
                answer = response.text.strip()
                logger.info("Gemini response received successfully via google-genai SDK.")
                return answer
            except ValueError as e:
                # Handle cases where response.text access fails (e.g., blocked content with no text part)
                logger.error(f"Could not extract text from Gemini response. Finish Reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}. Error: {e}. Response: {response}")
                raise Exception(f"Failed to get valid response content from Gemini API. Check logs for details.")

        except errors.APIError as e: # Catch specific API errors from the new SDK (Use APIError)
            logger.exception(f"Gemini API Error (google-genai): {e}")
            raise Exception(f"Error interacting with Gemini service (google-genai): {e}")
        except Exception as e:
            logger.exception(f"Unexpected error during Gemini SDK (google-genai) call: {e}")
            raise Exception(f"Unexpected error interacting with Gemini service (google-genai): {e}")

    def validate_api_key(self) -> bool:
        """
        Check if the Gemini API key is configured and the client was initialized.
        """
        # Check if the client object was successfully created in __init__
        return self.client is not None and self.api_key is not None and len(self.api_key) > 0