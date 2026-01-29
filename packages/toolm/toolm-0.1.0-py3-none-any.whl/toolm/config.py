from dataclasses import dataclass

@dataclass
class AgentConfig:
    """Configuration settings for the ToolM Agent."""
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.7
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192

    def to_generation_config(self):
        """Converts config to dictionary format for google-generativeai."""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }