"""
WatsonX Client - Adapted for openai/gpt-oss-120b quirks.

This client provides a standard WatsonX interface while internally adapting
for the vLLM backend bugs in IBM's gpt-oss-120b model hosting.

Usage:
    from watsonx_rlm_knowledge.watsonx_client import WatsonXClient, WatsonXConfig

    config = WatsonXConfig(
        api_key="your-api-key",
        project_id="your-project-id",
        region_url="https://us-south.ml.cloud.ibm.com"
    )

    client = WatsonXClient(config)

    # Chat (works directly)
    response = client.chat(messages=[{"role": "user", "content": "Hello"}])

    # Tools (adapted via prompt injection)
    response = client.chat_with_tools(
        messages=[{"role": "user", "content": "What's the weather?"}],
        tools=[{"type": "function", "function": {...}}]
    )

    # JSON schema (adapted via prompt injection)
    response = client.chat_with_json_schema(
        messages=[{"role": "user", "content": "Give me a recipe"}],
        schema={"type": "object", "properties": {...}}
    )
"""

from watsonx_rlm_knowledge.watsonx_client.client import WatsonXClient
from watsonx_rlm_knowledge.watsonx_client.config import WatsonXConfig
from watsonx_rlm_knowledge.watsonx_client.exceptions import (
    WatsonXError,
    WatsonXConnectionError,
    WatsonXAuthError,
    ToolExtractionError,
    JSONExtractionError,
    SchemaValidationError
)

__version__ = "1.0.0"
__all__ = [
    "WatsonXClient",
    "WatsonXConfig",
    "WatsonXError",
    "WatsonXConnectionError",
    "WatsonXAuthError",
    "ToolExtractionError",
    "JSONExtractionError",
    "SchemaValidationError",
]
