import os
import logging
import httpx
from typing import Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """
    Implementation of LLMProvider for OpenAI's API
    """
    def __init__(self):
        self.api_key = os.getenv("EXTERNAL_API_KEY")
        self.base_url = "https://api.openai.com/v1"
        logger.info("Initialized OpenAIProvider")

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using OpenAI API
        """
        if not self.validate_api_key():
            raise Exception("OpenAI API key not configured")
            
        logger.info(f"Generating response with OpenAI model: {model_id}")
        
        # Extract max_tokens if present in options
        max_tokens = options.get("max_tokens", 4096)
        temperature = options.get("temperature", 0.3)
        
        # Construct the messages format for ChatGPT models
        messages = [
            {"role": "system", "content": "You are a helpful assistant for the Islam West Africa Collection (IWAC)."},
            {"role": "user", "content": prompt}
        ]
        
        # Prepare the API request payload
        request_data = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # Add any other OpenAI-specific options
        for key, value in options.items():
            if key not in ["temperature", "max_tokens"]:
                request_data[key] = value
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        'Authorization': f"Bearer {self.api_key}",
                        'Content-Type': 'application/json'
                    },
                    json=request_data
                )
                response.raise_for_status()
                result = response.json()
                
                try:
                    answer = result["choices"][0]["message"]["content"].strip()
                    logger.info("OpenAI response received successfully")
                    return answer
                except (KeyError, IndexError, TypeError) as e:
                    logger.error(f"Failed to parse OpenAI response: {result}. Error: {e}")
                    raise Exception(f"Failed to parse response from OpenAI API: {e}")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with OpenAI API: {e}")
            raise Exception(f"Error communicating with OpenAI service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with OpenAI API: {e}")
            raise Exception(f"Unexpected error with OpenAI service: {e}")
    
    def validate_api_key(self) -> bool:
        """
        Check if the OpenAI API key is configured
        """
        return self.api_key is not None and len(self.api_key) > 0