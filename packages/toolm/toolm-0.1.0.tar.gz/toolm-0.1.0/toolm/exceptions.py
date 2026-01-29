class ToolMError(Exception):
    """Base exception for ToolM framework."""
    pass

class APIKeyMissingError(ToolMError):
    """Raised when the Gemini API Key is missing."""
    pass

class GenerationError(ToolMError):
    """Raised when the model fails to generate a response."""
    pass