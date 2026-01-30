"""Tool adapter for WatsonX.

Emulates function calling via prompt injection for models that don't
support native tool use (like openai/gpt-oss-120b on vLLM).
"""

import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple, Union, Callable

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    RetryError
)

from watsonx_rlm_knowledge.watsonx_client.exceptions import ToolExtractionError

logger = logging.getLogger(__name__)

try:
    import json_repair
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False


class EmptyResponseError(ToolExtractionError):
    """Model returned empty or thinking-only response."""
    pass


class ThinkingOnlyError(ToolExtractionError):
    """Model returned only internal thinking without actual content."""
    pass


TOOL_SYSTEM_PROMPT = """You are an AI assistant with access to tools/functions.

AVAILABLE TOOLS:
{tools_description}

TOOL USAGE INSTRUCTIONS:
When you need to use a tool, you MUST respond with ONLY a JSON object in this exact format:
{{
  "tool_calls": [
    {{
      "id": "call_<unique_id>",
      "type": "function",
      "function": {{
        "name": "<function_name>",
        "arguments": {{<arguments_as_json_object>}}
      }}
    }}
  ]
}}

CRITICAL RULES:
1. When using tools, output ONLY the JSON structure above - no other text
2. Start with {{ and end with }}
3. Use proper JSON syntax (double quotes, no trailing commas)
4. Arguments must be a valid JSON object, not a string

When NOT using tools, respond normally with helpful text.

{tool_choice_instruction}"""


class ToolAdapter:
    """Adapts tool/function calling for models without native support."""

    def __init__(self, max_retries: int = 3):
        """Initialize tool adapter."""
        self.max_retries = max_retries

    def format_tools_description(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools into human-readable description."""
        if not tools:
            return "No tools available."

        descriptions = []
        for tool in tools:
            if tool.get("type") != "function":
                continue

            func = tool.get("function", {})
            name = func.get("name", "unknown")
            desc = func.get("description", "No description")

            tool_desc = f"- {name}: {desc}"

            params = func.get("parameters", {})
            properties = params.get("properties", {})
            required = params.get("required", [])

            if properties:
                param_lines = []
                for param_name, param_info in properties.items():
                    param_type = param_info.get("type", "any")
                    req_marker = " (required)" if param_name in required else ""
                    param_desc = param_info.get("description", "")
                    if param_desc:
                        param_lines.append(f"    - {param_name}: {param_type}{req_marker} - {param_desc}")
                    else:
                        param_lines.append(f"    - {param_name}: {param_type}{req_marker}")

                if param_lines:
                    tool_desc += "\n" + "\n".join(param_lines)

            descriptions.append(tool_desc)

        return "\n".join(descriptions)

    def create_tool_system_message(
        self,
        tools: List[Dict[str, Any]],
        tool_choice: Union[str, Dict[str, Any]] = "auto"
    ) -> str:
        """Create system message for tool use."""
        if tool_choice == "none":
            return "You are a helpful assistant. Do not use any tools for this response."

        tools_description = self.format_tools_description(tools)
        tool_choice_instruction = ""

        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            func_name = tool_choice.get("function", {}).get("name", "")

            func_details = None
            for tool in tools:
                if tool.get("type") == "function":
                    if tool.get("function", {}).get("name") == func_name:
                        func_details = tool.get("function")
                        break

            if func_details:
                params_json = json.dumps(func_details.get("parameters", {}), indent=2)
                tool_choice_instruction = f"""
IMPORTANT: You MUST use the '{func_name}' function to respond.

The '{func_name}' function expects these parameters:
{params_json}

You MUST call this function with appropriate arguments."""

        elif tool_choice == "auto":
            tool_choice_instruction = "\nUse tools when appropriate to answer the user's query."

        return TOOL_SYSTEM_PROMPT.format(
            tools_description=tools_description,
            tool_choice_instruction=tool_choice_instruction
        )

    def inject_forced_function_example(
        self,
        messages: List[Dict[str, Any]],
        function_name: str,
        tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Inject an example of using the forced function."""
        if len(messages) > 2:
            return messages

        example_args = {}
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                if func.get("name") == function_name:
                    params = func.get("parameters", {})
                    properties = params.get("properties", {})
                    for prop_name, prop_info in properties.items():
                        prop_type = prop_info.get("type", "string")
                        if prop_type == "string":
                            example_args[prop_name] = f"example_{prop_name}"
                        elif prop_type in ("number", "integer"):
                            example_args[prop_name] = 42
                        elif prop_type == "boolean":
                            example_args[prop_name] = True
                        elif prop_type == "array":
                            example_args[prop_name] = []
                        elif prop_type == "object":
                            example_args[prop_name] = {}
                    break

        example_response = json.dumps({
            "tool_calls": [{
                "id": "call_example",
                "type": "function",
                "function": {
                    "name": function_name,
                    "arguments": example_args
                }
            }]
        }, indent=2)

        example_messages = [
            {"role": "user", "content": "Example: Please use the required function."},
            {"role": "assistant", "content": example_response}
        ]

        return messages[:1] + example_messages + messages[1:]

    def extract_tool_calls(
        self,
        response_text: str
    ) -> Tuple[bool, Optional[List[Dict[str, Any]]], Optional[str]]:
        """Extract tool calls from model response."""
        if not response_text:
            return False, None, "Empty response"

        cleaned = response_text.strip()

        if "```" in cleaned:
            pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
            matches = re.findall(pattern, cleaned, re.DOTALL)
            if matches:
                cleaned = matches[0].strip()

        json_start = cleaned.find("{")
        json_end = cleaned.rfind("}")

        if json_start == -1 or json_end == -1 or json_end <= json_start:
            indicators = ["tool_calls", '"name":', "function", "arguments"]
            if any(ind in cleaned.lower() for ind in indicators):
                return False, None, f"Response appears to contain tool call but no valid JSON"
            return False, None, "No JSON structure found in response"

        potential_json = cleaned[json_start:json_end + 1]

        try:
            data = json.loads(potential_json)
            if "tool_calls" in data and isinstance(data["tool_calls"], list):
                return True, data["tool_calls"], None
        except json.JSONDecodeError as e:
            logger.debug(f"Initial JSON parse failed: {e}")

            if HAS_JSON_REPAIR:
                try:
                    repaired = json_repair.repair_json(potential_json)
                    data = json.loads(repaired)
                    if "tool_calls" in data and isinstance(data["tool_calls"], list):
                        return True, data["tool_calls"], None
                except Exception as repair_error:
                    logger.debug(f"JSON repair failed: {repair_error}")

        indicators = ["tool_calls", '"name":', "function", "arguments"]
        if any(ind in cleaned.lower() for ind in indicators):
            return False, None, f"Failed to parse tool call JSON"

        return False, None, "No tool calls found in response"

    def validate_tool_call(
        self,
        tool_call: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """Validate a single tool call against available tools."""
        required_fields = ["id", "type", "function"]
        if not all(k in tool_call for k in required_fields):
            missing = [k for k in required_fields if k not in tool_call]
            return False, f"Missing required fields: {missing}"

        if tool_call.get("type") != "function":
            return False, f"Invalid type: {tool_call.get('type')}"

        func = tool_call.get("function", {})
        if not all(k in func for k in ["name", "arguments"]):
            return False, "Function missing name or arguments"

        func_name = func.get("name")
        matching_tool = None
        for tool in available_tools:
            if tool.get("type") == "function":
                if tool.get("function", {}).get("name") == func_name:
                    matching_tool = tool
                    break

        if not matching_tool:
            return False, f"Unknown function: {func_name}"

        if isinstance(func.get("arguments"), str):
            try:
                func["arguments"] = json.loads(func["arguments"])
            except json.JSONDecodeError:
                return False, "Invalid arguments JSON"
        elif not isinstance(func.get("arguments"), dict):
            return False, "Arguments must be a JSON object"

        tool_params = matching_tool.get("function", {}).get("parameters", {})
        required_params = tool_params.get("required", [])
        for param in required_params:
            if param not in func.get("arguments", {}):
                return False, f"Missing required parameter: {param}"

        return True, None

    def format_response(
        self,
        response_text: str,
        tools: List[Dict[str, Any]],
        tool_choice: Union[str, Dict[str, Any]] = "auto"
    ) -> Dict[str, Any]:
        """Format model response to OpenAI-compatible format."""
        if tool_choice == "none":
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }]
            }

        success, tool_calls, error = self.extract_tool_calls(response_text)

        if not success:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }]
            }

        valid_calls = []
        for tc in tool_calls:
            is_valid, err = self.validate_tool_call(tc, tools)
            if is_valid:
                if not tc.get("id"):
                    tc["id"] = f"call_{int(time.time() * 1000)}_{len(valid_calls)}"
                valid_calls.append(tc)
            else:
                logger.warning(f"Invalid tool call: {err}")

        if valid_calls:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": valid_calls
                    },
                    "finish_reason": "tool_calls"
                }]
            }
        else:
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }]
            }

    def _is_thinking_only(self, response_text: str) -> bool:
        """Check if response contains only thinking/reasoning."""
        if not response_text or not response_text.strip():
            return True

        text = response_text.strip().lower()

        thinking_patterns = [
            r"^<think>.*</think>$",
            r"^<thinking>.*</thinking>$",
            r"^let me think.*$",
        ]

        for pattern in thinking_patterns:
            if re.match(pattern, text, re.DOTALL | re.IGNORECASE):
                return True

        if len(text) < 3:
            return True

        if text.startswith("<think>") and "</think>" in text:
            after_think = text.split("</think>", 1)[-1].strip()
            if not after_think:
                return True

        return False

    def _validate_response(self, response_text: str) -> str:
        """Validate response is not empty or thinking-only."""
        if not response_text:
            raise EmptyResponseError("Model returned empty response")

        if self._is_thinking_only(response_text):
            raise ThinkingOnlyError(f"Model returned thinking-only: {response_text[:100]}...")

        text = response_text.strip()
        if "<think>" in text.lower() and "</think>" in text.lower():
            parts = re.split(r"</think>", text, flags=re.IGNORECASE)
            if len(parts) > 1:
                after_think = parts[-1].strip()
                if after_think:
                    return after_think

        return text

    def process_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        model_call_fn: Callable[[List[Dict[str, Any]]], str],
        tool_choice: Union[str, Dict[str, Any]] = "auto"
    ) -> Dict[str, Any]:
        """Process a request with tools via prompt injection."""
        from watsonx_rlm_knowledge.watsonx_client.adapters.message_adapter import MessageAdapter

        if tool_choice == "none":
            response = model_call_fn(messages)
            return self.format_response(response, tools, tool_choice)

        system_content = self.create_tool_system_message(tools, tool_choice)
        modified_messages = MessageAdapter.inject_system_message(
            messages.copy(), system_content, replace=True
        )

        forced_function = None
        if isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            forced_function = tool_choice.get("function", {}).get("name", "")
            modified_messages = self.inject_forced_function_example(
                modified_messages, forced_function, tools
            )

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=10),
            retry=retry_if_exception_type((ToolExtractionError, EmptyResponseError, ThinkingOnlyError)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def attempt_tool_call():
            response_text = model_call_fn(modified_messages)
            response_text = self._validate_response(response_text)

            result = self.format_response(response_text, tools, tool_choice)

            message = result.get("choices", [{}])[0].get("message", {})
            if message.get("tool_calls"):
                if forced_function:
                    actual = message["tool_calls"][0].get("function", {}).get("name", "")
                    if actual != forced_function:
                        raise ToolExtractionError(
                            f"Model called {actual} instead of forced {forced_function}"
                        )
                return result

            indicators = ["tool_calls", '"name":', "function", "arguments"]
            if any(ind in response_text.lower() for ind in indicators):
                raise ToolExtractionError("Failed to extract valid tool calls")

            if forced_function:
                raise ToolExtractionError("Model did not use the forced function")

            return result

        try:
            return attempt_tool_call()
        except RetryError as e:
            last_error = e.last_attempt.exception() if e.last_attempt else e
            logger.error(f"Tool calling failed after {self.max_retries} attempts: {last_error}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"Error using tools: {last_error}"
                    },
                    "finish_reason": "stop"
                }]
            }
        except (ToolExtractionError, EmptyResponseError, ThinkingOnlyError) as e:
            logger.error(f"Tool calling failed: {e}")
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"Error using tools: {e}"
                    },
                    "finish_reason": "stop"
                }]
            }
