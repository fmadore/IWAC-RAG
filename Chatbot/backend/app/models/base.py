from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class LLMProvider(ABC):
    """
    Abstract base class for LLM providers
    """
    @abstractmethod
    async def generate(self, prompt: str, model_id: str, options: Dict[str, Any]) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            model_id: The specific model ID to use
            options: Additional options for the model
            
        Returns:
            The generated text response
        """
        pass
    
    @abstractmethod
    def validate_api_key(self) -> bool:
        """
        Validate that the required API key for this provider is available.
        
        Returns:
            True if valid, False otherwise
        """
        pass