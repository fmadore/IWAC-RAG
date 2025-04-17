import os
import logging
import anthropic
from typing import Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """
    Implementation of LLMProvider for Anthropic's API (Claude models)
    """
    def __init__(self):
        # The Anthropic client automatically uses ANTHROPIC_API_KEY env var
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            logger.info("Initialized AnthropicProvider (API key found)")
        else:
            logger.warning("Anthropic API key not found in environment.")
            # The validate_api_key method will handle checks before generation

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using Anthropic API
        """
        if not self.validate_api_key():
            raise Exception("Anthropic API key not configured")

        logger.info(f"Generating response with Anthropic model: {model_id}")

        # Extract relevant options or use defaults
        max_tokens = options.get("maxOutputTokens", 1024) # Use maxOutputTokens from config
        temperature = options.get("temperature", 0.3)

        # Anthropic API expects system prompt + user message
        # The ModelManager constructs the prompt including context and user question.
        # We can try to separate the initial system part from the user-specific part.
        # Split strategy: Everything before "User question:" is system prompt.
        parts = prompt.split("\n\nUser question:", 1)
        if len(parts) == 2:
            system_prompt = parts[0].strip()
            user_message = f"User question: {parts[1].strip()}"
        else:
            # Fallback if the specific separator isn't found
            system_prompt = "Vous êtes un assistant utile pour la Collection Islam Afrique de l'Ouest (IWAC). Répondez à la question en vous basant sur le contexte fourni."
            user_message = prompt # Treat the whole prompt as the user message
        
        # Ensure system prompt is not empty
        if not system_prompt:
             system_prompt = "Vous êtes un assistant utile pour la Collection Islam Afrique de l'Ouest (IWAC). Répondez à la question en vous basant sur le contexte fourni."

        messages = [
            {"role": "user", "content": user_message}
        ]

        try:
            # Use the async client for FastAPI integration
            # Initialize it here to ensure it uses the correct key context
            async_client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # Use streaming API
            response_chunks = []
            async with async_client.messages.stream(
                model=model_id,
                system=system_prompt,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                async for text in stream.text_stream:
                    response_chunks.append(text)
            
            answer = "".join(response_chunks)
            logger.info("Anthropic streaming response received successfully")
            return answer.strip()

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            # Provide more context if possible, e.g., status code
            details = f"Status Code: {e.status_code}, Message: {e.message}" if hasattr(e, 'status_code') else str(e)
            raise Exception(f"Error communicating with Anthropic service: {details}")
        except Exception as e:
            logger.exception(f"Unexpected error with Anthropic API call: {e}") # Use logger.exception for traceback
            raise Exception(f"Unexpected error during Anthropic API call: {e}")

    def validate_api_key(self) -> bool:
        """
        Check if the Anthropic API key is configured via environment variable.
        """
        # Check the stored key from __init__
        return self.api_key is not None and len(self.api_key) > 0 