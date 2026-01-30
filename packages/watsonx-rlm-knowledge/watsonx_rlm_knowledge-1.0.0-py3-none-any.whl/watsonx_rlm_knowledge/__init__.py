"""
RLM Knowledge Client - Domain Knowledge Query System

This package provides an RLM (Recursive Language Model) based client that uses
local filesystem documents as domain knowledge for LLM-powered queries.

The system:
1. Indexes documents in a specified directory (including PDF, DOCX, XLSX, PPTX)
2. Provides lazy, on-demand access to document content
3. Uses the RLM pattern where the LLM writes Python to explore the knowledge base
4. Returns synthesized answers based on relevant document content

Usage:
    from watsonx_rlm_knowledge import KnowledgeClient
    
    # Initialize with a knowledge directory
    client = KnowledgeClient.from_directory("/path/to/documents")
    
    # Or with explicit WatsonX credentials
    client = KnowledgeClient.from_credentials(
        knowledge_root="/path/to/documents",
        api_key="your-api-key",
        project_id="your-project-id"
    )
    
    # Query the knowledge base
    answer = client.query("How does the authentication system work?")
    print(answer)
    
    # Chat with context
    response = client.chat([
        {"role": "user", "content": "Explain the database schema"}
    ])
"""

from watsonx_rlm_knowledge.client import KnowledgeClient
from watsonx_rlm_knowledge.context import KnowledgeContext, KnowledgeContextConfig
from watsonx_rlm_knowledge.engine import RLMEngine
from watsonx_rlm_knowledge.preprocessor import DocumentPreprocessor
from watsonx_rlm_knowledge.exceptions import (
    RLMKnowledgeError,
    PreprocessingError,
    ContextError,
    EngineError,
)

__version__ = "1.0.0"
__all__ = [
    "KnowledgeClient",
    "KnowledgeContext",
    "KnowledgeContextConfig",
    "RLMEngine",
    "DocumentPreprocessor",
    "RLMKnowledgeError",
    "PreprocessingError",
    "ContextError",
    "EngineError",
]
