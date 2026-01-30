"""
WatsonX Client - Facade for openai/gpt-oss-120b with vLLM bug adaptations.

This client provides a standard WatsonX interface while internally handling
the quirks of IBM's vLLM backend for the gpt-oss-120b model.

Features that work directly:
- Basic chat completions
- Streaming responses

Features that require adaptation (prompt injection):
- Tool/function calling
- JSON schema responses
- JSON object mode

Known WatsonX quirks handled:
- Model sometimes returns only 'reasoning_content' without actual 'content'
  (thinking-only responses) - we retry automatically
"""

import json
import logging
import time
import uuid
import threading
import atexit
from typing import Dict, List, Any, Optional, Union, Iterator, Tuple

from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential

from watsonx_rlm_knowledge.watsonx_client.config import WatsonXConfig
from watsonx_rlm_knowledge.watsonx_client.exceptions import (
    WatsonXError,
    WatsonXConnectionError,
    WatsonXAuthError,
    ModelNotReadyError,
    ThinkingOnlyResponseError,
)
from watsonx_rlm_knowledge.watsonx_client.adapters import ToolAdapter, JSONSchemaAdapter, MessageAdapter

logger = logging.getLogger(__name__)

# Lazy import for IBM SDK
_ibm_sdk_available = None
_ModelInference = None
_APIClient = None
_Credentials = None
_WMLClientError = None


def _check_ibm_sdk():
    """Check and import IBM SDK lazily."""
    global _ibm_sdk_available, _ModelInference, _APIClient, _Credentials, _WMLClientError
    
    if _ibm_sdk_available is not None:
        return _ibm_sdk_available
    
    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.wml_client_error import WMLClientError
        
        _ModelInference = ModelInference
        _APIClient = APIClient
        _Credentials = Credentials
        _WMLClientError = WMLClientError
        _ibm_sdk_available = True
    except ImportError:
        _ibm_sdk_available = False
    
    return _ibm_sdk_available


# Connection pool for client reuse
_client_pool: Dict[str, Any] = {}
_client_pool_lock = threading.Lock()
_max_clients = 5


class WatsonXClient:
    """WatsonX client with transparent adaptation for gpt-oss-120b quirks.

    This client presents a standard interface matching what a properly-working
    WatsonX model would expose. Internally, it adapts requests as needed to
    work around vLLM backend bugs.

    Example:
        config = WatsonXConfig(
            api_key="your-key",
            project_id="your-project",
            region_url="https://us-south.ml.cloud.ibm.com"
        )
        client = WatsonXClient(config)

        # Basic chat (works directly)
        response = client.chat([{"role": "user", "content": "Hello"}])

        # With tools (adapted via prompt injection)
        response = client.chat_with_tools(
            messages=[{"role": "user", "content": "What's the weather?"}],
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather for a location",
                    "parameters": {...}
                }
            }]
        )
    """

    def __init__(self, config: WatsonXConfig):
        """Initialize client.

        Args:
            config: WatsonX configuration

        Raises:
            WatsonXAuthError: If credentials are invalid
            WatsonXConnectionError: If connection fails
        """
        if not _check_ibm_sdk():
            raise ImportError(
                "IBM WatsonX SDK not available. Install with: pip install ibm-watsonx-ai"
            )
        
        self.config = config
        self._model = None
        self._api_client = None
        self._cleaned_up = False
        self._active_streams: List[Any] = []

        # Adapters for handling quirks
        self._tool_adapter = ToolAdapter(max_retries=config.max_retries)
        self._json_adapter = JSONSchemaAdapter(max_retries=config.max_retries + 2)

        # Initialize connection
        self._initialize()

    def _initialize(self):
        """Initialize IBM API client and model."""
        if not self.config.validate():
            raise WatsonXAuthError("Invalid configuration: missing required fields")

        try:
            self._api_client = self._get_cached_client()

            credentials = _Credentials(
                url=self.config.region_url,
                api_key=self.config.api_key
            )

            self._model = _ModelInference(
                model_id=self.config.model_id,
                params=self.config.get_generation_params(),
                credentials=credentials,
                project_id=self.config.project_id,
                api_client=self._api_client
            )

            logger.info(f"Initialized WatsonX client for model: {self.config.model_id}")

        except _WMLClientError as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise WatsonXAuthError(f"Authentication failed: {e}")
            raise WatsonXConnectionError(f"Connection failed: {e}")
        except Exception as e:
            raise WatsonXConnectionError(f"Failed to initialize: {e}")

    def _get_cached_client(self):
        """Get or create a cached API client."""
        client_key = f"{self.config.region_url}:{self.config.project_id}"

        with _client_pool_lock:
            if client_key in _client_pool:
                logger.debug(f"Reusing cached client for {client_key}")
                return _client_pool[client_key]

            if len(_client_pool) >= _max_clients:
                oldest_key = next(iter(_client_pool))
                old_client = _client_pool.pop(oldest_key)
                if hasattr(old_client, "close"):
                    try:
                        old_client.close()
                    except:
                        pass
                logger.info(f"Evicted cached client: {oldest_key}")

            credentials = _Credentials(
                url=self.config.region_url,
                api_key=self.config.api_key
            )
            client = _APIClient(credentials=credentials, project_id=self.config.project_id)
            _client_pool[client_key] = client
            logger.info(f"Created new cached client for {client_key}")

            return client

    def _ensure_ready(self):
        """Ensure model is ready for use."""
        if self._cleaned_up or self._model is None:
            raise ModelNotReadyError("Client has been cleaned up or not initialized")

    def cleanup(self):
        """Clean up resources."""
        if self._cleaned_up:
            return

        for stream in self._active_streams:
            try:
                if hasattr(stream, "close"):
                    stream.close()
            except:
                pass
        self._active_streams.clear()

        self._model = None
        self._api_client = None
        self._cleaned_up = True

        logger.debug(f"Cleaned up WatsonX client for {self.config.model_id}")

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()

    # =========================================================================
    # Core Chat Methods
    # =========================================================================

    def chat(
        self,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Send a chat completion request.

        Args:
            messages: List of messages in OpenAI format
            stream: If True, return a streaming iterator
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            OpenAI-compatible response dict, or iterator if streaming
        """
        self._ensure_ready()

        params = self._normalize_params(kwargs)
        adapted_messages = MessageAdapter.adapt_messages(messages)
        formatted_messages = MessageAdapter.format_for_api(adapted_messages)

        if stream:
            return self._stream_chat(formatted_messages, params)
        else:
            return self._sync_chat(formatted_messages, params)

    def _normalize_params(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parameter names for the API."""
        params = {}

        if "max_new_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_new_tokens"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]

        for key in ["temperature", "top_p", "repetition_penalty", "reasoning_effort"]:
            if key in kwargs:
                params[key] = kwargs[key]

        return params

    def _sync_chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Synchronous chat completion with automatic retry for thinking-only responses."""
        call_kwargs = {"messages": messages}
        if params:
            call_kwargs["params"] = params

        @retry(
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(ThinkingOnlyResponseError),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True
        )
        def _call_with_retry():
            result = self._model.chat(**call_kwargs)

            if isinstance(result, str):
                if not result.strip():
                    raise ThinkingOnlyResponseError("(empty string response)")
                return self._format_response(result)

            if isinstance(result, dict):
                if "choices" in result and result["choices"]:
                    message = result["choices"][0].get("message", {})
                    content = message.get("content", "")
                    reasoning = message.get("reasoning_content", "")

                    if not content and reasoning:
                        if self._is_actual_response(reasoning):
                            logger.info("Using reasoning_content as response")
                            result["choices"][0]["message"]["content"] = reasoning
                            content = reasoning
                        else:
                            logger.warning(f"Model returned thinking-only response, retrying")
                            raise ThinkingOnlyResponseError(reasoning)

                    if not content and not reasoning:
                        logger.warning("Model returned empty response, retrying")
                        raise ThinkingOnlyResponseError("(empty response)")

                    for choice in result["choices"]:
                        if "message" in choice and "refusal" not in choice["message"]:
                            choice["message"]["refusal"] = None

                return result

            if result is None:
                raise ThinkingOnlyResponseError("(None response)")

            return self._format_response(str(result))

        try:
            return _call_with_retry()
        except ThinkingOnlyResponseError as e:
            logger.error(f"Failed after retries: {e}")
            raise WatsonXError(
                f"Model failed to produce content after 3 retries. "
                f"Last response was thinking-only: {e.reasoning_preview[:200]}"
            )
        except _WMLClientError as e:
            logger.error(f"WatsonX API error: {e}")
            raise WatsonXError(f"Chat failed: {e}")

    def _is_actual_response(self, text: str) -> bool:
        """Check if text contains an actual response vs just thinking."""
        if not text:
            return False

        stripped = text.strip()

        if stripped.startswith("{") or stripped.startswith("#") or stripped.startswith("```"):
            return True

        if '```json' in text:
            return True

        extracted_json = self._try_extract_json(text)
        if extracted_json is not None:
            return True

        return False

    def _try_extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text."""
        if not text:
            return None

        original = text

        if "```json" in text:
            try:
                start = text.index("```json") + 7
                end = text.index("```", start)
                text = text[start:end].strip()
            except ValueError:
                pass
        elif "```" in text:
            try:
                start = text.index("```") + 3
                end = text.index("```", start)
                extracted = text[start:end].strip()
                if extracted.startswith("{"):
                    text = extracted
            except ValueError:
                pass

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        text = original
        brace_start = text.find("{")
        if brace_start == -1:
            return None

        depth = 0
        in_string = False
        escape_next = False
        brace_end = -1

        for i in range(brace_start, len(text)):
            char = text[i]

            if escape_next:
                escape_next = False
                continue

            if char == "\\":
                escape_next = True
                continue

            if char == '"' and not escape_next:
                in_string = not in_string
                continue

            if in_string:
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    brace_end = i + 1
                    break

        if brace_end == -1:
            return None

        json_str = text[brace_start:brace_end]

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        import re
        fixed = re.sub(r',\s*([}\]])', r'\1', json_str)
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

        return None

    def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        params: Optional[Dict[str, Any]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Streaming chat completion."""
        stream = None
        try:
            call_kwargs = {"messages": messages}
            if params:
                call_kwargs["params"] = params
            stream = self._model.chat_stream(**call_kwargs)
            self._active_streams.append(stream)

            for chunk in stream:
                if isinstance(chunk, dict) and "choices" in chunk:
                    yield chunk
                elif chunk is not None:
                    yield self._format_stream_chunk(str(chunk))

        except _WMLClientError as e:
            logger.error(f"Stream error: {e}")
            yield self._format_stream_chunk(f"[ERROR: {e}]", finish_reason="error")
        finally:
            if stream and stream in self._active_streams:
                self._active_streams.remove(stream)
                if hasattr(stream, "close"):
                    try:
                        stream.close()
                    except:
                        pass

    # =========================================================================
    # Tool/Function Calling (Adapted via Prompt Injection)
    # =========================================================================

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with tool/function calling support."""
        self._ensure_ready()

        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._tool_adapter.process_with_tools(
            messages=adapted_messages,
            tools=tools,
            model_call_fn=model_call_fn,
            tool_choice=tool_choice
        )

        return self._add_response_metadata(response)

    # =========================================================================
    # JSON Schema Responses (Adapted via Prompt Injection)
    # =========================================================================

    def chat_with_json_schema(
        self,
        messages: List[Dict[str, Any]],
        schema: Dict[str, Any],
        schema_name: str = "response",
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with JSON schema enforcement."""
        self._ensure_ready()

        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._json_adapter.process_with_schema(
            messages=adapted_messages,
            schema=schema,
            model_call_fn=model_call_fn,
            schema_name=schema_name
        )

        return self._add_response_metadata(response)

    def chat_with_json_object(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Chat with simple JSON object mode."""
        self._ensure_ready()

        adapted_messages = MessageAdapter.adapt_messages(messages)

        def model_call_fn(msgs: List[Dict[str, Any]]) -> str:
            formatted = MessageAdapter.format_for_api(msgs)
            result = self._model.chat(messages=formatted)
            if isinstance(result, dict) and "choices" in result:
                return result["choices"][0].get("message", {}).get("content", "")
            return str(result) if result else ""

        response = self._json_adapter.process_json_object(
            messages=adapted_messages,
            model_call_fn=model_call_fn
        )

        return self._add_response_metadata(response)

    # =========================================================================
    # Unified Chat Method (Matches OpenAI Interface)
    # =========================================================================

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Union[str, Dict[str, Any]] = "auto",
        response_format: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Unified chat completion matching OpenAI's interface."""
        if tools:
            if stream:
                logger.warning("Streaming not supported with tools")
            return self.chat_with_tools(messages, tools, tool_choice, **kwargs)

        if response_format:
            if stream:
                logger.warning("Streaming not supported with response_format")

            format_type = response_format.get("type")

            if format_type == "json_schema":
                json_schema = response_format.get("json_schema", {})
                schema = json_schema.get("schema", {})
                schema_name = json_schema.get("name", "response")
                return self.chat_with_json_schema(messages, schema, schema_name, **kwargs)

            elif format_type == "json_object":
                return self.chat_with_json_object(messages, **kwargs)

        return self.chat(messages, stream=stream, **kwargs)

    # =========================================================================
    # Text Generation (Non-Chat)
    # =========================================================================

    def generate(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> Union[str, Iterator[str]]:
        """Generate text from a prompt."""
        self._ensure_ready()

        if stream:
            return self._stream_generate(prompt)
        else:
            result = self._model.generate_text(prompt=prompt)
            return result

    def _stream_generate(self, prompt: str) -> Iterator[str]:
        """Streaming text generation."""
        stream = None
        try:
            stream = self._model.generate_text_stream(prompt=prompt)
            self._active_streams.append(stream)

            for chunk in stream:
                if chunk:
                    yield str(chunk) if not isinstance(chunk, str) else chunk

        finally:
            if stream and stream in self._active_streams:
                self._active_streams.remove(stream)

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _format_response(self, content: str) -> Dict[str, Any]:
        """Format a string response to OpenAI-compatible format."""
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.config.model_id,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                    "refusal": None
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    def _format_stream_chunk(
        self,
        content: str,
        finish_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Format a streaming chunk."""
        return {
            "id": f"chatcmpl-{uuid.uuid4().hex[:29]}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": self.config.model_id,
            "choices": [{
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason
            }]
        }

    def _add_response_metadata(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Add standard metadata fields to response."""
        if "id" not in response:
            response["id"] = f"chatcmpl-{uuid.uuid4().hex[:29]}"
        if "object" not in response:
            response["object"] = "chat.completion"
        if "created" not in response:
            response["created"] = int(time.time())
        if "model" not in response:
            response["model"] = self.config.model_id
        if "usage" not in response:
            response["usage"] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        return response


def _cleanup_all_clients():
    """Clean up all cached clients."""
    with _client_pool_lock:
        for key, client in _client_pool.items():
            try:
                if hasattr(client, "close"):
                    client.close()
            except:
                pass
        _client_pool.clear()

atexit.register(_cleanup_all_clients)
