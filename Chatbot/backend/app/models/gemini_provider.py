import os
import logging
from typing import Dict, Any
from .base import LLMProvider
import google.generativeai as genai
from google.generativeai import types # Explicitly import types

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    Implementation of LLMProvider for Google's Gemini API using the google-genai SDK.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None # Initialize client as None
        if self.api_key:
            try:
                # Use genai.Client for initialization
                self.client = genai.Client(api_key=self.api_key)
                # Test connection with a simple listing - optional but good practice
                # self.client.list_models() # This would make init potentially blocking/async
                logger.info("GeminiProvider initialized with genai.Client.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")
                self.api_key = None # Mark as unconfigured if client fails
                self.client = None
        else:
            logger.warning("GEMINI_API_KEY not found in environment.")
            self.api_key = None # Ensure api_key is None if not found

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using the google-genai SDK via Client.
        """
        # Check if the client was initialized successfully
        if not self.client:
            raise Exception("Gemini Client not initialized. Check API key and configuration.")

        logger.info(f"Generating response with Gemini model: {model_id} using google-genai SDK")

        try:
            # Prepare generation config using types.GenerationConfig
            # Filter out None values explicitly for GenerationConfig arguments
            gen_config_dict = {
                "temperature": options.get("temperature", 0.3),
                 # No default for max_output_tokens in GenerationConfig, handle None
            }
            max_tokens = options.get("maxOutputTokens")
            if max_tokens is not None:
                gen_config_dict["max_output_tokens"] = int(max_tokens) # Ensure it's an int

            # Add other supported options if present, e.g., top_p, top_k
            if options.get("topP") is not None:
                 gen_config_dict["top_p"] = options.get("topP")
            if options.get("topK") is not None:
                 gen_config_dict["top_k"] = options.get("topK")
            # Add stop sequences if provided
            stop_sequences = options.get("stopSequences")
            if stop_sequences and isinstance(stop_sequences, list):
                gen_config_dict["stop_sequences"] = stop_sequences


            generation_config = types.GenerationConfig(**gen_config_dict)


            # Prepare contents in the required format (list of Content parts)
            # For simple text prompt, structure it as user role
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]

            # Model ID might need the 'models/' prefix depending on usage context
            # The client methods generally handle this, but being explicit can be safer.
            # If model_id already contains "models/", this won't hurt.
            # If not, like "gemini-1.5-flash", it becomes "models/gemini-1.5-flash".
            full_model_id = f"models/{model_id}" if not model_id.startswith("models/") else model_id

            # Generate content asynchronously using the client
            response = await self.client.generate_content_async(
                model=full_model_id, # Use the full model ID
                contents=contents,
                generation_config=generation_config
                # Add safety_settings and tools here if needed later
            )

            # Extract the text response (structure remains similar)
            if response.candidates and response.candidates[0].content.parts:
                # Check if parts exist before accessing
                if response.candidates[0].content.parts:
                    answer = response.candidates[0].content.parts[0].text.strip()
                    logger.info("Gemini response received successfully via Client SDK.")
                    return answer
                else:
                     logger.error(f"Gemini response candidate missing parts. Response: {response}")
                     raise Exception("Gemini response candidate missing parts.")
            elif hasattr(response, 'prompt_feedback') and getattr(response.prompt_feedback, 'block_reason', None):
                block_reason = response.prompt_feedback.block_reason
                # Get more details if available
                block_details = ""
                if hasattr(response.prompt_feedback, 'safety_ratings'):
                    block_details = f" Safety Ratings: {response.prompt_feedback.safety_ratings}"
                logger.error(f"Gemini request blocked. Reason: {block_reason}.{block_details}")
                raise Exception(f"Content blocked by Gemini API due to: {block_reason}.{block_details}")
            else:
                # Handle cases where response might be empty or malformed
                logger.error(f"Gemini response missing expected content or blocked without specific reason. Response: {response}")
                # Check for finish_reason if available
                finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN') if response.candidates else 'NO_CANDIDATES'
                if finish_reason != "STOP": # Should be STOP for successful generation
                     raise Exception(f"Gemini generation finished unexpectedly. Reason: {finish_reason}. Response: {response}")
                else: # Should not happen if candidate structure is correct, but as fallback
                    raise Exception(f"Failed to get valid response content from Gemini API. Finish Reason: {finish_reason}. Response: {response}")


        except Exception as e:
            logger.exception(f"Error during Gemini Client SDK call: {e}")
            # Re-raise exceptions to be handled upstream, potentially adding context
            raise Exception(f"Error interacting with Gemini service via Client SDK: {e}")

    def validate_api_key(self) -> bool:
        """Check if the Gemini API key is configured and client initialized."""
        return self.api_key is not None and len(self.api_key) > 0 and self.client is not None