import os
import google.generativeai as genai
from typing import Optional, List, Dict, Any
from .config import AgentConfig
from .exceptions import APIKeyMissingError, GenerationError

class Agent:
    """
    The main Agent class for ToolM.
    
    Attributes:
        api_key (str): Google Gemini API Key.
        config (AgentConfig): Configuration for generation parameters.
        history (List): Chat history.
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[AgentConfig] = None, system_instruction: Optional[str] = None):
        """
        Initialize the ToolM Agent.

        Args:
            api_key (str): Your Gemini API Key. If None, checks os.environ['GEMINI_API_KEY'].
            config (AgentConfig): Optional configuration object.
            system_instruction (str): Optional system prompt to define agent behavior.
        """
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

        Args:
            query (str): The user's input text.

        Returns:
            str: The agent's response.
        """
        if not query:
            return ""

        try:
            response = self._chat_session.send_message(query)
            return response.text
        except Exception as e:
            raise GenerationError(f"Error during generation: {str(e)}")

    def clear_memory(self):
        """Resets the conversation history."""
        self._chat_session = self._model.start_chat(history=[])

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Returns the raw history from the internal Gemini chat session."""
        return self._chat_session.history