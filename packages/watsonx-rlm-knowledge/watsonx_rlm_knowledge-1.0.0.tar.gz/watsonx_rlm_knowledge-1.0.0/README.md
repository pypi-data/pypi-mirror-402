# RLM Knowledge Client

A portable Python package for querying local document knowledge bases using the **Recursive Language Model (RLM)** pattern with IBM WatsonX as the LLM backend.

## Overview

This package allows you to:

1. **Index a directory of documents** - including PDF, DOCX, XLSX, PPTX, and all text files
2. **Query the knowledge base** - using natural language questions
3. **Get AI-synthesized answers** - based on relevant document content

The key innovation is the **RLM pattern**: instead of dumping all documents into the context (which fails for large knowledge bases), the LLM writes Python code to explore the documents on-demand, searching and reading only what's needed.

## Installation

```bash
# From source
pip install -e /path/to/watsonx_rlm_knowledge

# Or install directly
pip install watsonx-rlm-knowledge
```

## Quick Start

### 1. Set Environment Variables

```bash
export WATSONX_API_KEY="your-ibm-cloud-api-key"
export WATSONX_PROJECT_ID="your-watsonx-project-id"
export RLM_KNOWLEDGE_ROOT="/path/to/your/documents"

# Optional
export WATSONX_REGION_URL="https://us-south.ml.cloud.ibm.com"  # default
export WATSONX_MODEL_ID="openai/gpt-oss-120b"  # default
```

### 2. Use the Client

```python
from watsonx_rlm_knowledge import KnowledgeClient

# Initialize client (preprocesses documents automatically)
client = KnowledgeClient.from_directory("/path/to/documents")

# Query the knowledge base
answer = client.query("How does the authentication system work?")
print(answer)

# Get detailed results
result = client.query_detailed("Explain the database schema")
print(f"Answer: {result.answer}")
print(f"Iterations: {result.iterations}")
print(f"Time: {result.total_time:.2f}s")
```

### 3. Or Use the CLI

```bash
# Query
watsonx-rlm-knowledge query "How does authentication work?"

# Interactive chat
watsonx-rlm-knowledge chat

# List documents
watsonx-rlm-knowledge list

# Search
watsonx-rlm-knowledge search "authentication"

# Statistics
watsonx-rlm-knowledge stats
```

## Supported Document Formats

### Text Files (read directly)
- Code: `.py`, `.js`, `.ts`, `.java`, `.c`, `.cpp`, `.go`, `.rs`, `.rb`, etc.
- Config: `.json`, `.yaml`, `.toml`, `.xml`, `.ini`, etc.
- Documentation: `.md`, `.txt`, `.rst`, `.tex`, etc.
- Web: `.html`, `.css`, `.vue`, `.svelte`, etc.
- Data: `.csv`, `.sql`, `.graphql`, etc.

### Binary Documents (converted to text)
- PDF: `.pdf`
- Word: `.docx`, `.doc`
- Excel: `.xlsx`, `.xls`
- PowerPoint: `.pptx`, `.ppt`
- Other: `.rtf`, `.odt`, `.ods`, `.odp`

## How It Works

### The RLM Pattern

Traditional RAG (Retrieval-Augmented Generation) has limitations:
- Embedding search may miss relevant content
- Context windows can't hold large documents
- Pre-chunking loses document structure

**RLM (Recursive Language Model)** takes a different approach:

1. The LLM is given access to a **KnowledgeContext** object
2. It writes **Python code** to explore documents
3. Code is **executed** and results fed back
4. The LLM iterates until it has enough information
5. Finally outputs a **FINAL_ANSWER**

```
User Query → LLM writes Python → Execute → Results → LLM writes more Python → ... → FINAL_ANSWER
```

### Example RLM Iteration

```python
# LLM writes this code:
matches = knowledge.search("authentication")
obs = f"Found {len(matches)} matches for 'authentication':\n"
for m in matches[:5]:
    obs += f"  {m.path}:{m.line_number}: {m.line_text}\n"

# Results fed back:
# "Found 12 matches for 'authentication':
#   auth/login.py:45: def authenticate_user(username, password):
#   docs/api.md:23: ## Authentication Methods
#   ..."

# LLM then reads the relevant file:
content = knowledge.read_slice("auth/login.py", offset=0, nbytes=5000)
obs = content

# And continues until it can answer the question
```

## API Reference

### KnowledgeClient

The main interface for querying knowledge bases.

```python
# Factory methods
client = KnowledgeClient.from_directory("/path/to/docs")
client = KnowledgeClient.from_credentials(
    knowledge_root="/path/to/docs",
    api_key="your-key",
    project_id="your-project"
)
client = KnowledgeClient.from_env()

# Query methods
answer = client.query("question")
result = client.query_detailed("question")  # Returns RLMResult

# Utility methods
docs = client.list_documents(pattern="*.pdf")
results = client.search("term", max_results=20)
content = client.read_document("path/to/doc.md")
stats = client.get_stats()
client.preprocess(force=True)
```

### KnowledgeContext

Low-level access to the knowledge base (used by the RLM engine).

```python
from watsonx_rlm_knowledge import KnowledgeContext

ctx = KnowledgeContext("/path/to/docs")

# List documents
docs = ctx.list_documents()
files = ctx.list_files()

# Search
matches = ctx.search("term", max_matches=50)
matches = ctx.grep("pattern")
matches = ctx.search_regex(r"auth\w+")

# Read content
text = ctx.head("doc.md", nbytes=5000)
text = ctx.read_slice("doc.md", offset=1000, nbytes=3000)
text = ctx.read_full("doc.md")
text = ctx.tail("doc.md")

# Document info
toc = ctx.get_table_of_contents("doc.md")
count = ctx.count_occurrences("authentication")
```

### RLMEngine

The core engine that runs the RLM loop.

```python
from watsonx_rlm_knowledge import RLMEngine, KnowledgeContext
from watsonx_rlm_knowledge.engine import RLMConfig

# Custom configuration
config = RLMConfig(
    max_iterations=15,      # Max exploration iterations
    max_code_retries=3,     # Retries for code errors
    temperature=0.1,        # LLM temperature
    main_max_tokens=4096,   # Max tokens for main calls
    subcall_max_tokens=2048 # Max tokens for subcalls
)

# Create engine
engine = RLMEngine(
    knowledge=ctx,
    llm_call_fn=your_llm_function,
    config=config
)

# Run query
result = engine.run("Your question here")
print(result.answer)
print(result.iterations)
print(result.observations)
```

### DocumentPreprocessor

Handles conversion of binary documents to text.

```python
from watsonx_rlm_knowledge import DocumentPreprocessor
from watsonx_rlm_knowledge.preprocessor import PreprocessorConfig

config = PreprocessorConfig(
    cache_dir=".rlm_cache",
    max_file_size_mb=50,
    skip_hidden=True,
    skip_dirs=(".git", "node_modules", "__pycache__")
)

preprocessor = DocumentPreprocessor("/path/to/docs", config)
preprocessor.preprocess_all(force=False)

# Get text content
text = preprocessor.get_text("/path/to/docs/report.pdf")
```

## Configuration

### WatsonX Configuration

```python
from watsonx_rlm_knowledge.watsonx_client import WatsonXConfig

config = WatsonXConfig(
    api_key="your-key",
    project_id="your-project",
    region_url="https://us-south.ml.cloud.ibm.com",
    model_id="openai/gpt-oss-120b",
    max_tokens=8192,
    temperature=0.1,
    reasoning_effort="low"  # Reduces "thinking-only" outputs
)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `WATSONX_API_KEY` | IBM Cloud API key | (required) |
| `WATSONX_PROJECT_ID` | WatsonX project ID | (required) |
| `WATSONX_REGION_URL` | WatsonX region URL | `https://us-south.ml.cloud.ibm.com` |
| `WATSONX_MODEL_ID` | Model ID | `openai/gpt-oss-120b` |
| `RLM_KNOWLEDGE_ROOT` | Default knowledge directory | (none) |

## CLI Reference

```bash
# Query the knowledge base
watsonx-rlm-knowledge query "Your question here"
watsonx-rlm-knowledge query "Your question" --detailed

# Interactive chat mode
watsonx-rlm-knowledge chat

# List documents
watsonx-rlm-knowledge list
watsonx-rlm-knowledge list --pattern "*.pdf"
watsonx-rlm-knowledge list --json

# Search documents
watsonx-rlm-knowledge search "term"
watsonx-rlm-knowledge search "term" --max-results 50

# Preprocess documents
watsonx-rlm-knowledge preprocess
watsonx-rlm-knowledge preprocess --force

# Show statistics
watsonx-rlm-knowledge stats
watsonx-rlm-knowledge stats --json

# Read a document
watsonx-rlm-knowledge read "path/to/doc.md"
watsonx-rlm-knowledge read "path/to/doc.md" --max-bytes 10000

# Global options
watsonx-rlm-knowledge --knowledge-root /path/to/docs query "question"
watsonx-rlm-knowledge --verbose query "question"
```

## WatsonX Adapters

The WatsonX client includes adapters to work around bugs in IBM's vLLM backend:

### Tool Adapter
Emulates function calling via prompt injection when native tool use is broken.

### JSON Adapter
Enforces JSON schema responses via prompt engineering.

### Message Adapter
Handles vLLM quirks like null content issues.

### Thinking Handler
Automatically retries when the model returns only "reasoning_content" without actual output.

## Example Use Cases

### Code Documentation Q&A

```python
client = KnowledgeClient.from_directory("./my-project")
answer = client.query("How do I configure the database connection?")
```

### Research Paper Analysis

```python
client = KnowledgeClient.from_directory("./papers")
answer = client.query("What are the main findings about transformer architectures?")
```

### Policy Document Search

```python
client = KnowledgeClient.from_directory("./policies")
answer = client.query("What is the vacation policy for remote employees?")
```

## Troubleshooting

### "WatsonX credentials not found"
Ensure you've set `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` environment variables.

### "Model returned thinking-only response"
The client automatically retries, but if this persists, try:
- Setting `reasoning_effort="low"` in WatsonXConfig
- Simplifying your query

### Slow preprocessing
Large PDFs or many documents take time. Progress is cached, so subsequent runs are faster.

### Document not found
Ensure the path is relative to your knowledge root, not absolute.

## License

MIT License

## Contributing

Contributions welcome! Please open an issue or PR.
