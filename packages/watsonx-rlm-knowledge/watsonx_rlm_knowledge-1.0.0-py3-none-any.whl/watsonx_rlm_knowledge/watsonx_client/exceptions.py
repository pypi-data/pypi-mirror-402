"""Custom exceptions for WatsonX client."""


class WatsonXError(Exception):
    """Base exception for WatsonX client errors."""
    pass


class WatsonXConnectionError(WatsonXError):
    """Connection or network-related errors."""
    pass


class WatsonXAuthError(WatsonXError):
    """Authentication or authorization errors."""
    pass


class ToolExtractionError(WatsonXError):
    """Failed to extract tool calls from model response."""
    pass


class JSONExtractionError(WatsonXError):
    """Failed to extract valid JSON from model response."""
    pass


class SchemaValidationError(WatsonXError):
    """JSON response doesn't match expected schema."""
    pass


class ModelNotReadyError(WatsonXError):
    """Model has been cleaned up or is not initialized."""
    pass


class ThinkingOnlyResponseError(WatsonXError):
    """Model returned only reasoning/thinking content without actual response.

    This happens when WatsonX returns a response with 'reasoning_content' but
    empty 'content'. The client will automatically retry when this occurs.
    """

    def __init__(self, reasoning_preview: str = ""):
        self.reasoning_preview = reasoning_preview
        super().__init__(
            f"Model returned only thinking content without actual response. "
            f"Preview: {reasoning_preview[:200]}..."
        )
