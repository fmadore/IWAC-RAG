import os
import logging
from typing import Dict, Any
from .base import LLMProvider
import google.generativeai as genai
from google.generativeai.types import GenerationConfig, SafetySetting, HarmCategory
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger(__name__)

# Configure safety settings to be less restrictive
# Adjust these as needed based on your use case and acceptable risk
safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": SafetySetting.HarmBlockThreshold.BLOCK_NONE,
    },
]

class GeminiProvider(LLMProvider):
    """
    Implementation of LLMProvider for Google's Gemini API using the google-genai SDK.
    """
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                logger.info("GeminiProvider initialized and configured.")
            except Exception as e:
                logger.error(f"Failed to configure Gemini SDK: {e}")
                # Decide if initialization should fail or proceed without configuration
                self.api_key = None # Mark as unconfigured
        else:
            logger.warning("GEMINI_API_KEY not found in environment.")
            self.api_key = None

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using the google-genai SDK.
        """
        if not self.validate_api_key():
            raise Exception("Gemini API key not configured or SDK initialization failed")

        logger.info(f"Generating response with Gemini model: {model_id}")

        try:
            # Get the model instance
            model = genai.GenerativeModel(model_id)

            # Prepare generation config
            sdk_options = {
                "temperature": options.get("temperature", 0.3),
                # Map maxOutputTokens if present in config
                "max_output_tokens": options.get("maxOutputTokens"), 
                # Add other potential mappings like top_p, top_k if needed
                # "top_p": options.get("topP"),
                # "top_k": options.get("topK"),
            }
            # Filter out None values, as the SDK expects explicit values or omission
            sdk_options = {k: v for k, v in sdk_options.items() if v is not None}
            generation_config = GenerationConfig(**sdk_options)

            # Generate content asynchronously
            # The entire prompt constructed by ModelManager is sent as a single user message
            response = await model.generate_content_async(
                contents=prompt, 
                generation_config=generation_config,
                safety_settings=safety_settings # Apply configured safety settings
            )

            # Extract the text response
            # Handle potential lack of response or empty parts
            if response.candidates and response.candidates[0].content.parts:
                answer = response.candidates[0].content.parts[0].text.strip()
                logger.info("Gemini response received successfully via SDK.")
                return answer
            elif response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason
                 logger.error(f"Gemini request blocked. Reason: {block_reason}")
                 raise Exception(f"Content blocked by Gemini API due to: {block_reason}")
            else:
                logger.error(f"Gemini response missing expected content. Response: {response}")
                raise Exception("Failed to get valid response content from Gemini API.")

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Gemini SDK API error: {e}")
            raise Exception(f"Error communicating with Gemini service via SDK: {e}")
        except Exception as e:
            # Catch potential SDK-specific errors or unexpected issues
            logger.exception(f"Unexpected error during Gemini SDK call: {e}")
            raise Exception(f"Unexpected error with Gemini service via SDK: {e}")

    def validate_api_key(self) -> bool:
        """
        Check if the Gemini API key was successfully configured.
        """
        # Check if the key was present and configuration succeeded
        return self.api_key is not None