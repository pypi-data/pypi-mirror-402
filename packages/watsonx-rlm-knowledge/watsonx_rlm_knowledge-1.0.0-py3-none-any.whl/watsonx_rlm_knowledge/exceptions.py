"""Custom exceptions for RLM Knowledge Client."""


class RLMKnowledgeError(Exception):
    """Base exception for RLM Knowledge Client errors."""
    pass


class PreprocessingError(RLMKnowledgeError):
    """Error during document preprocessing/conversion."""
    pass


class ContextError(RLMKnowledgeError):
    """Error accessing or reading knowledge context."""
    pass


class EngineError(RLMKnowledgeError):
    """Error during RLM engine execution."""
    pass


class ConfigurationError(RLMKnowledgeError):
    """Invalid or missing configuration."""
    pass


class WatsonXBackendError(RLMKnowledgeError):
    """Error communicating with WatsonX backend."""
    pass


class MaxIterationsError(EngineError):
    """RLM loop exceeded maximum iterations without final answer."""
    pass


class CodeExecutionError(EngineError):
    """Error executing model-generated Python code."""
    pass
