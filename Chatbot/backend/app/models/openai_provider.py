import os
import logging
import openai # Use the official library
from typing import Dict, Any
from .base import LLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """
    Implementation of LLMProvider for OpenAI's API using the openai library.
    """
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Initialize the async client
        if self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            logger.info("Initialized OpenAIProvider with openai.AsyncOpenAI client.")
        else:
            self.client = None
            logger.warning("OPENAI_API_KEY not found. OpenAIProvider client not initialized.")

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using OpenAI API via the openai library.
        """
        if not self.validate_api_key():
            raise Exception("OpenAI API key not configured or client not initialized.")

        logger.info(f"Generating response with OpenAI model: {model_id} using official SDK")

        # Extract relevant options
        max_tokens = options.get("max_tokens", 4096)
        temperature = options.get("temperature", 0.3)

        # Construct the messages format
        # Note: ModelManager constructs the full prompt including context + user query.
        # The chat completions endpoint expects a structured message list.
        # A simple approach is to pass the entire prompt as a user message.
        # A more sophisticated approach might split system instructions from user query.
        messages = [
            # Optionally add a system message if needed, or rely on the prompt structure from ModelManager
            # {"role": "system", "content": "Vous êtes un assistant utile."},
            {"role": "user", "content": prompt}
        ]

        # Prepare the arguments for the API call
        # Filter out None values or keys not recognized by the API if necessary
        api_kwargs = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            # Add other supported parameters from options if they exist
        }

        # Add any other OpenAI-specific options from the config if they are valid API parameters
        # Example: top_p, frequency_penalty, presence_penalty
        for key, value in options.items():
            if key not in ["temperature", "max_tokens"] and hasattr(openai.types.chat.CompletionCreateParamsBase, key):
                 # Basic check if the key might be a valid parameter
                 api_kwargs[key] = value


        try:
            response = await self.client.chat.completions.create(**api_kwargs)

            if response.choices and response.choices[0].message and response.choices[0].message.content:
                answer = response.choices[0].message.content.strip()
                logger.info("OpenAI response received successfully via SDK.")
                return answer
            else:
                # Log the full response if structure is unexpected
                logger.error(f"Unexpected OpenAI response format: {response}")
                finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
                raise Exception(f"Failed to get valid content from OpenAI API response. Finish reason: {finish_reason}")

        except openai.APIError as e:
            # Handle API errors (e.g., rate limits, server errors)
            logger.error(f"OpenAI API error: Status={e.status_code}, Message={e.message}, Type={e.type}, Code={e.code}")
            # Provide specific details if available in the error body
            error_details = getattr(e, 'body', {}).get('error', {}).get('message', str(e))
            raise Exception(f"OpenAI API Error ({e.status_code}): {error_details}")
        except Exception as e:
            # Handle other potential errors (network issues, etc.)
            logger.exception(f"Unexpected error during OpenAI API call: {e}") # Log traceback
            raise Exception(f"Unexpected error communicating with OpenAI service: {e}")

    def validate_api_key(self) -> bool:
        """
        Check if the OpenAI API key is configured and the client is initialized.
        """
        return self.api_key is not None and len(self.api_key) > 0 and self.client is not None