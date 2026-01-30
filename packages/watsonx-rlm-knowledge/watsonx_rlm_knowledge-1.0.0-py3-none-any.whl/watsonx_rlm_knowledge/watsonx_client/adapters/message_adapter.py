"""Message adapter for WatsonX compatibility.

Handles the quirks of message formatting required for the vLLM backend.
"""

import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class MessageAdapter:
    """Adapts messages for WatsonX/vLLM compatibility.

    Key adaptations:
    - Ensures content is never None (vLLM chokes on null content)
    - Converts 'tool' role messages to assistant messages with tags
    - Adds placeholder content for tool-calling messages without content
    """

    @staticmethod
    def adapt_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Adapt messages for WatsonX compatibility.

        Args:
            messages: List of OpenAI-format messages

        Returns:
            Adapted messages safe for WatsonX/vLLM
        """
        adapted = []

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content")

            if role == "tool":
                # Convert tool responses to user messages (vLLM handles this better)
                # Format as clean JSON to avoid parsing issues
                tool_content = content or ""
                adapted.append({
                    "role": "user",
                    "content": f"Function returned: {tool_content}"
                })

            elif role == "assistant" and msg.get("tool_calls") and content is None:
                # For assistant messages with tool calls, include the call info as content
                tool_calls = msg.get("tool_calls", [])
                if tool_calls:
                    call_info = tool_calls[0]
                    func_name = call_info.get("function", {}).get("name", "unknown")
                    func_args = call_info.get("function", {}).get("arguments", {})
                    adapted.append({
                        "role": "assistant",
                        "content": f"I will call {func_name} with arguments: {func_args}"
                    })
                else:
                    adapted.append({
                        "role": "assistant",
                        "content": "I will call a function."
                    })

            else:
                # Ensure content is never None
                msg_copy = msg.copy()
                if msg_copy.get("content") is None:
                    msg_copy["content"] = ""
                # Strip tool_calls from the copy to avoid vLLM issues
                if "tool_calls" in msg_copy:
                    del msg_copy["tool_calls"]
                adapted.append(msg_copy)

        return adapted

    @staticmethod
    def format_for_api(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format messages for the IBM API.

        Strips down to just role and content.

        Args:
            messages: Adapted messages

        Returns:
            Minimal message format for IBM API
        """
        return [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content") or ""
            }
            for msg in messages
        ]

    @staticmethod
    def inject_system_message(
        messages: List[Dict[str, Any]],
        system_content: str,
        replace: bool = True
    ) -> List[Dict[str, Any]]:
        """Inject or replace system message.

        Args:
            messages: Original messages
            system_content: New system message content
            replace: If True, replace existing system message; if False, prepend

        Returns:
            Messages with system message injected
        """
        messages = messages.copy()
        system_message = {"role": "system", "content": system_content}

        # Find existing system message
        system_index = next(
            (i for i, msg in enumerate(messages) if msg.get("role") == "system"),
            None
        )

        if system_index is not None:
            if replace:
                messages[system_index] = system_message
            else:
                # Prepend to existing system message
                existing = messages[system_index].get("content", "")
                messages[system_index] = {
                    "role": "system",
                    "content": f"{system_content}\n\n{existing}"
                }
        else:
            # Insert at beginning
            messages.insert(0, system_message)

        return messages

    @staticmethod
    def extract_last_assistant_content(messages: List[Dict[str, Any]]) -> Optional[str]:
        """Extract content from the last assistant message.

        Args:
            messages: List of messages

        Returns:
            Content of last assistant message, or None
        """
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                return msg.get("content")
        return None
