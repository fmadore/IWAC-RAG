import os
import logging
import httpx
from typing import Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class GeminiProvider(LLMProvider):
    """
    Implementation of LLMProvider for Google's Gemini API
    """
    def __init__(self):
        self.api_key = os.getenv("EXTERNAL_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        logger.info("Initialized GeminiProvider")

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using Gemini API
        """
        if not self.validate_api_key():
            raise Exception("Gemini API key not configured")
            
        logger.info(f"Generating response with Gemini model: {model_id}")
        
        # Construct API URL with the provided model ID
        api_url = f"{self.base_url}/{model_id}:generateContent?key={self.api_key}"
        
        # Prepare generation config with options or defaults
        generation_config = {
            "temperature": options.get("temperature", 0.3)
        }
        
        # Add max output tokens if specified
        if "maxOutputTokens" in options:
            generation_config["maxOutputTokens"] = options["maxOutputTokens"]
        
        # Construct the request payload
        request_payload = {
            "contents": [{
                "parts":[{"text": prompt}]
            }],
            "generationConfig": generation_config
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    api_url,
                    headers={'Content-Type': 'application/json'},
                    json=request_payload
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract text from the response
                try:
                    answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                    logger.info("Gemini response received successfully")
                    return answer
                except (KeyError, IndexError, TypeError) as e:
                    logger.error(f"Failed to parse Gemini response: {result}. Error: {e}")
                    raise Exception(f"Failed to parse response from Gemini API: {e}")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with Gemini API: {e}")
            raise Exception(f"Error communicating with Gemini service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with Gemini API: {e}")
            raise Exception(f"Unexpected error with Gemini service: {e}")
    
    def validate_api_key(self) -> bool:
        """
        Check if the Gemini API key is configured
        """
        return self.api_key is not None and len(self.api_key) > 0