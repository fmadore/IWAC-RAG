import os
import logging
from typing import Dict, Any
from .base import LLMProvider
import google.generativeai as genai
from google.generativeai import types # Keep explicit types import

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    Implementation of LLMProvider for Google's Gemini API using the google-generativeai SDK.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.configured = False # Flag to track successful configuration
        if self.api_key:
            try:
                # Configure the library with the API key
                genai.configure(api_key=self.api_key)
                # Perform a simple test, like listing models, to validate the key (optional but recommended)
                # Note: This makes __init__ potentially blocking if not handled carefully
                # For simplicity here, we assume configuration is enough for basic validation
                # Or we could perform a quick list_models check
                # Example check (can be blocking):
                # models_list = [m for m in genai.list_models()] # Basic check
                # if not models_list:
                #    raise Exception("API key might be invalid or no models accessible.")
                self.configured = True
                logger.info("GeminiProvider configured successfully with google-generativeai.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini Client/SDK: {e}")
                self.api_key = None # Mark as unconfigured if setup fails
        else:
            logger.warning("GEMINI_API_KEY not found in environment.")
            self.api_key = None # Ensure api_key is None if not found

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using the google-generativeai SDK.
        """
        # Check if the library was configured successfully during init
        if not self.validate_api_key():
            raise Exception("Gemini SDK not configured. Check API key and initial setup.")

        logger.info(f"Generating response with Gemini model: {model_id} using google-generativeai SDK")

        try:
            # Create the GenerativeModel instance
            # Model ID might need the 'models/' prefix, let's ensure it
            full_model_id = f"models/{model_id}" if not model_id.startswith("models/") else model_id
            model = genai.GenerativeModel(full_model_id)

            # Prepare generation config using types.GenerationConfig
            gen_config_dict = {
                "temperature": options.get("temperature", 0.3),
            }
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

            generation_config = types.GenerationConfig(**gen_config_dict)

            # Generate content asynchronously using the model instance
            # The prompt from ModelManager includes context and query
            response = await model.generate_content_async(
                contents=prompt, # Pass the combined prompt string directly
                generation_config=generation_config
                # Add safety_settings here if needed later
            )

            # Extract the text response
            if response.candidates and response.candidates[0].content.parts:
                if response.candidates[0].content.parts:
                    answer = response.candidates[0].content.parts[0].text.strip()
                    logger.info("Gemini response received successfully via SDK.")
                    return answer
                else:
                     logger.error(f"Gemini response candidate missing parts. Response: {response}")
                     raise Exception("Gemini response candidate missing parts.")
            elif hasattr(response, 'prompt_feedback') and getattr(response.prompt_feedback, 'block_reason', None):
                block_reason = response.prompt_feedback.block_reason
                block_details = ""
                if hasattr(response.prompt_feedback, 'safety_ratings'):
                    block_details = f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
                logger.error(f"Gemini request blocked. Reason: {block_reason}.{block_details}")
                raise Exception(f"Content blocked by Gemini API due to: {block_reason}.{block_details}")
            else:
                logger.error(f"Gemini response missing expected content or blocked. Response: {response}")
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if response.candidates else 'NO_CANDIDATES'
                raise Exception(f"Failed to get valid response content from Gemini API. Finish Reason: {finish_reason}. Response: {response}")

        except Exception as e:
            logger.exception(f"Error during Gemini SDK call: {e}")
            raise Exception(f"Error interacting with Gemini service via SDK: {e}")

    def validate_api_key(self) -> bool:
        """
        Check if the Gemini API key is configured and SDK was initialized.
        """
        # Check the configured flag set during __init__
        return self.configured and self.api_key is not None and len(self.api_key) > 0