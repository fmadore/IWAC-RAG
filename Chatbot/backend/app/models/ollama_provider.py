import os
import logging
import httpx
from typing import Dict, Any, Optional
from .base import LLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(LLMProvider):
    """
    Implementation of LLMProvider for Ollama
    """
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        logger.info(f"Initialized OllamaProvider with base URL: {self.base_url}")

    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate text using Ollama API
        """
        logger.info(f"Generating response with Ollama model: {model_id}")
        
        # Merge provided options with defaults
        request_options = options.copy() if options else {}
        
        # Prepare the API request
        request_data = {
            "model": model_id,
            "prompt": prompt,
            "stream": False,
            "options": request_options
        }
        
        # Add temperature if provided
        if "temperature" in options:
            request_data["temperature"] = options["temperature"]
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=request_data
                )
                response.raise_for_status()
                result = response.json()
                answer = result.get("response", "").strip()
                logger.info(f"Ollama response generated successfully")
                return answer
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error with Ollama API: {e}")
            raise Exception(f"Error communicating with Ollama service: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with Ollama API: {e}")
            raise Exception(f"Unexpected error with Ollama service: {e}")
    
    def validate_api_key(self) -> bool:
        """
        Ollama doesn't require an API key, so this always returns True
        """
        return True