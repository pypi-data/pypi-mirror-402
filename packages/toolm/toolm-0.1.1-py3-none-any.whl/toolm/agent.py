import os
import google.generativeai as genai
from typing import Optional, List, Dict, Any
from google.api_core.exceptions import NotFound
from .config import AgentConfig
from .exceptions import APIKeyMissingError, GenerationError

class Agent:
    """
    The main Agent class for ToolM.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[AgentConfig] = None, system_instruction: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise APIKeyMissingError("Gemini API Key is required. Pass it to the constructor or set GEMINI_API_KEY env var.")

        self.config = config if config else AgentConfig()
        
        # Configure the Google Library
        genai.configure(api_key=self.api_key)

        # Initialize Model
        try:
            self._model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=self.config.to_generation_config(),
                system_instruction=system_instruction
            )
            # Start a chat session (memory)
            self._chat_session = self._model.start_chat(history=[])
        except Exception as e:
            raise GenerationError(f"Failed to initialize Gemini model: {str(e)}")

    def run(self, query: str) -> str:
        """
        Sends a query to the agent and returns the response.
        """
        if not query:
            return ""

        try:
            response = self._chat_session.send_message(query)
            return response.text
        except NotFound:
            # Specific handling for the 404 error you encountered
            available = self.get_available_models(self.api_key)
            raise GenerationError(
                f"Model '{self.config.model_name}' not found or not supported. "
                f"Your API Key has access to: {available}"
            )
        except Exception as e:
            raise GenerationError(f"Error during generation: {str(e)}")

    def clear_memory(self):
        """Resets the conversation history."""
        self._chat_session = self._model.start_chat(history=[])

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Returns the raw history."""
        return self._chat_session.history

    @staticmethod
    def get_available_models(api_key: str = None) -> List[str]:
        """
        Helper method to list models available to the provided API Key.
        """
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            return []
        
        genai.configure(api_key=key)
        try:
            models = genai.list_models()
            # Filter for models that support generating content
            return [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        except Exception:
            return ["Could not fetch models"]