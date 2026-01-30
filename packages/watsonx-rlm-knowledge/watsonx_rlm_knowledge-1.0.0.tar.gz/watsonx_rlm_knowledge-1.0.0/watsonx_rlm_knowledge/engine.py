"""
RLM Engine - Recursive Language Model execution engine.

This implements the RLM pattern where:
1. The model receives a query
2. It writes Python code to explore the knowledge base
3. Code is executed and results fed back
4. Repeat until FINAL_ANSWER is produced

The model has access to:
- knowledge: KnowledgeContext instance for exploring documents
- subcall(text): Function to make recursive LLM calls on excerpts
"""

import logging
import re
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from watsonx_rlm_knowledge.context import KnowledgeContext
from watsonx_rlm_knowledge.exceptions import (
    EngineError,
    MaxIterationsError,
    CodeExecutionError,
)

logger = logging.getLogger(__name__)


# Pattern to extract Python code blocks
CODE_BLOCK_PATTERN = re.compile(
    r"```python\s*(.*?)\s*```",
    re.DOTALL | re.IGNORECASE
)

# Pattern to detect final answer
FINAL_ANSWER_PATTERN = re.compile(
    r"FINAL_ANSWER:\s*(.*)",
    re.DOTALL
)


# RLM System prompt that instructs the model how to use the knowledge context
RLM_SYSTEM_PROMPT = """You are operating in an RLM (Recursive Language Model) loop with access to a knowledge base.

You do NOT have the full document contents in your prompt.
Instead, you have access to a Python REPL environment with:

AVAILABLE OBJECTS:
- knowledge: A KnowledgeContext instance for exploring documents
- subcall(text: str) -> str: Calls the same model on smaller text excerpts

KNOWLEDGE CONTEXT METHODS:
- knowledge.list_files() -> List[str]: List all document paths
- knowledge.list_documents(pattern=None) -> List[DocumentSummary]: List documents with metadata
- knowledge.head(path, nbytes=32000) -> str: Read beginning of document
- knowledge.read_slice(path, offset=0, nbytes=50000) -> str: Read section of document
- knowledge.read_full(path) -> str: Read entire document (up to limit)
- knowledge.search(needle, max_matches=100) -> List[SearchMatch]: Search across all documents
- knowledge.grep(needle, max_matches=50) -> List[(path, line_no, text)]: Simple grep
- knowledge.search_regex(pattern) -> List[SearchMatch]: Regex search
- knowledge.find_files(pattern) -> List[str]: Find files by glob pattern
- knowledge.get_table_of_contents(path) -> List[str]: Get document structure/headings
- knowledge.count_occurrences(needle) -> int: Count string occurrences

SEARCH MATCH ATTRIBUTES:
- match.path: Document path
- match.line_number: Line number
- match.line_text: The matching line

RULES:
1) When you need to explore the knowledge base, output a Python code block:
```python
# Your code here using 'knowledge' and/or 'subcall'
# Store your findings in the variable 'obs' (observation)
obs = ""  # This will be shown to you
```

2) When you have enough information to answer, output:
FINAL_ANSWER: <your comprehensive answer here>

STRATEGY:
1. Start by listing files or searching for relevant terms
2. Use search() or grep() to find where topics are discussed
3. Use read_slice() to read relevant sections
4. Use subcall() to summarize long sections if needed
5. Synthesize findings into FINAL_ANSWER

Be efficient - prefer targeted searches over reading entire documents.
Store intermediate findings in the 'obs' variable to track your progress.

IMPORTANT: 
- Always output EITHER a code block OR FINAL_ANSWER, never both
- The 'obs' variable contents will be shown to you after code execution
- If you encounter errors, adjust your approach and try again
"""


@dataclass
class RLMConfig:
    """Configuration for RLM engine."""
    max_iterations: int = 15
    max_code_retries: int = 3
    subcall_max_tokens: int = 2048
    main_max_tokens: int = 4096
    temperature: float = 0.1
    timeout_per_iteration: float = 60.0
    safe_execution: bool = True  # Restrict what code can do
    include_traceback: bool = True


@dataclass
class RLMResult:
    """Result from RLM execution."""
    answer: str
    iterations: int
    total_time: float
    observations: List[str] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    success: bool = True


class RLMEngine:
    """Executes RLM loops for knowledge base queries.
    
    The engine manages the conversation with the LLM, executes Python
    code blocks that the LLM generates, and tracks the exploration
    until a final answer is produced.
    
    Example:
        engine = RLMEngine(knowledge, llm_call_fn)
        result = engine.run("How does the authentication system work?")
        print(result.answer)
    """
    
    def __init__(
        self,
        knowledge: KnowledgeContext,
        llm_call_fn: Callable[[List[Dict[str, Any]]], str],
        config: Optional[RLMConfig] = None,
    ):
        """Initialize RLM engine.
        
        Args:
            knowledge: Knowledge context for document access
            llm_call_fn: Function to call the LLM with messages
            config: Optional engine configuration
        """
        self.knowledge = knowledge
        self.llm_call_fn = llm_call_fn
        self.config = config or RLMConfig()
        
        # Execution namespace for code
        self._namespace: Dict[str, Any] = {}
        self._reset_namespace()
    
    def _reset_namespace(self):
        """Reset the execution namespace."""
        self._namespace = {
            "knowledge": self.knowledge,
            "subcall": self._subcall,
            # Safe builtins
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "any": any,
            "all": all,
            "print": self._safe_print,
            "isinstance": isinstance,
            "type": type,
            "repr": repr,
            # For string manipulation
            "re": re,
            # Result variable
            "obs": "",
        }
    
    def _safe_print(self, *args, **kwargs):
        """Safe print that captures to obs."""
        output = " ".join(str(a) for a in args)
        current_obs = self._namespace.get("obs", "")
        if current_obs:
            self._namespace["obs"] = current_obs + "\n" + output
        else:
            self._namespace["obs"] = output
    
    def _subcall(self, text: str) -> str:
        """Make a recursive LLM call on a text excerpt.
        
        Used for summarizing long sections or answering sub-questions.
        """
        sub_messages = [
            {
                "role": "system",
                "content": (
                    "You are a subcall in an RLM loop. "
                    "Answer based ONLY on the provided excerpt. "
                    "Be concise and factual."
                )
            },
            {"role": "user", "content": text},
        ]
        
        try:
            return self.llm_call_fn(
                sub_messages,
                temperature=self.config.temperature,
                max_tokens=self.config.subcall_max_tokens,
            )
        except Exception as e:
            logger.warning(f"Subcall failed: {e}")
            return f"(subcall error: {e})"
    
    def run(
        self,
        query: str,
        system_prompt: Optional[str] = None,
        additional_context: str = "",
    ) -> RLMResult:
        """Run RLM loop to answer a query.
        
        Args:
            query: The user's question about the knowledge base
            system_prompt: Optional custom system prompt
            additional_context: Additional context to include
        
        Returns:
            RLMResult with answer and execution metadata
        """
        start_time = time.time()
        self._reset_namespace()
        
        # Build initial messages
        system_content = system_prompt or RLM_SYSTEM_PROMPT
        if additional_context:
            system_content += f"\n\nADDITIONAL CONTEXT:\n{additional_context}"
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": query},
        ]
        
        result = RLMResult(
            answer="",
            iterations=0,
            total_time=0.0,
        )
        
        code_retry_count = 0
        
        for iteration in range(self.config.max_iterations):
            result.iterations = iteration + 1
            
            try:
                # Get LLM response
                model_response = self.llm_call_fn(
                    messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.main_max_tokens,
                )
                
                if not model_response:
                    logger.warning("Empty model response")
                    messages.append({"role": "assistant", "content": ""})
                    messages.append({
                        "role": "user",
                        "content": "Your response was empty. Please try again."
                    })
                    continue
                
                logger.debug(f"Iteration {iteration + 1}: {model_response[:200]}...")
                
                # Check for final answer
                if self._is_final_answer(model_response):
                    result.answer = self._extract_final_answer(model_response)
                    result.success = True
                    break
                
                # Extract and execute code
                code = self._extract_code(model_response)
                
                if code:
                    result.code_blocks.append(code)
                    
                    # Execute the code
                    exec_result = self._execute_code(code)
                    
                    if exec_result["success"]:
                        obs = exec_result["observation"]
                        result.observations.append(obs)
                        code_retry_count = 0  # Reset on success
                        
                        # Add to conversation
                        messages.append({"role": "assistant", "content": model_response})
                        messages.append({
                            "role": "user",
                            "content": f"Observation from executed code:\n{obs}\n\nContinue exploring or provide FINAL_ANSWER."
                        })
                    else:
                        error_msg = exec_result["error"]
                        result.errors.append(error_msg)
                        code_retry_count += 1
                        
                        if code_retry_count >= self.config.max_code_retries:
                            # Force to final answer on repeated failures
                            messages.append({"role": "assistant", "content": model_response})
                            messages.append({
                                "role": "user",
                                "content": (
                                    f"Code execution failed repeatedly: {error_msg}\n\n"
                                    "Please provide FINAL_ANSWER based on what you know so far."
                                )
                            })
                        else:
                            messages.append({"role": "assistant", "content": model_response})
                            messages.append({
                                "role": "user",
                                "content": f"Code execution error: {error_msg}\n\nPlease fix the code and try again."
                            })
                else:
                    # No code block found - guide back on track
                    messages.append({"role": "assistant", "content": model_response})
                    messages.append({
                        "role": "user",
                        "content": (
                            "Please output ONLY one of:\n"
                            "1. A ```python``` code block to explore the knowledge base, OR\n"
                            "2. FINAL_ANSWER: followed by your answer\n\n"
                            "Do not include explanations with the code block."
                        )
                    })
            
            except Exception as e:
                logger.error(f"Iteration {iteration + 1} failed: {e}")
                result.errors.append(str(e))
                
                # Try to continue
                messages.append({
                    "role": "user",
                    "content": f"An error occurred: {e}\n\nPlease continue or provide FINAL_ANSWER."
                })
        
        # Check if we exhausted iterations
        if not result.answer:
            result.success = False
            result.answer = (
                "I was unable to provide a complete answer within the iteration limit. "
                f"I explored the knowledge base for {result.iterations} iterations.\n\n"
                f"Observations gathered:\n" + 
                "\n---\n".join(result.observations[-3:]) if result.observations else "(none)"
            )
        
        result.total_time = time.time() - start_time
        return result
    
    def _is_final_answer(self, text: str) -> bool:
        """Check if response contains final answer."""
        return "FINAL_ANSWER:" in text
    
    def _extract_final_answer(self, text: str) -> str:
        """Extract the final answer from response."""
        match = FINAL_ANSWER_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        
        # Fallback: everything after FINAL_ANSWER:
        idx = text.find("FINAL_ANSWER:")
        if idx != -1:
            return text[idx + 13:].strip()
        
        return text
    
    def _extract_code(self, text: str) -> Optional[str]:
        """Extract Python code from response."""
        match = CODE_BLOCK_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        
        # Fallback: if it looks like Python code (has knowledge. calls)
        if "knowledge." in text and not "FINAL_ANSWER" in text:
            # Try to extract code-like portion
            lines = []
            in_code = False
            for line in text.split("\n"):
                if "knowledge." in line or "subcall(" in line or "obs" in line:
                    in_code = True
                    lines.append(line)
                elif in_code and line.strip() and not line.startswith(("#", "/*", "*")):
                    if any(kw in line for kw in ["for", "if", "=", "print", "obs"]):
                        lines.append(line)
            
            if lines:
                return "\n".join(lines)
        
        return None
    
    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute Python code in restricted namespace.
        
        Returns:
            Dict with 'success', 'observation', and optionally 'error'
        """
        # Reset obs
        self._namespace["obs"] = ""
        
        # Basic safety checks
        if self.config.safe_execution:
            forbidden = [
                "import ", "__import__", "exec(", "eval(",
                "open(", "os.", "sys.", "subprocess",
                "__builtins__", "__globals__", "__locals__",
                "compile(", "getattr(", "setattr(",
            ]
            for pattern in forbidden:
                if pattern in code:
                    return {
                        "success": False,
                        "error": f"Forbidden operation: {pattern}",
                        "observation": "",
                    }
        
        try:
            # Execute with timeout would require threading
            # For now, trust the code (it's from our LLM)
            exec(code, {"__builtins__": {}}, self._namespace)
            
            obs = self._namespace.get("obs", "")
            if not obs:
                obs = "(Code executed successfully but no observation stored in 'obs')"
            
            return {
                "success": True,
                "observation": str(obs)[:10000],  # Cap observation size
                "error": None,
            }
        
        except Exception as e:
            error_msg = str(e)
            if self.config.include_traceback:
                error_msg += "\n" + traceback.format_exc()
            
            return {
                "success": False,
                "observation": "",
                "error": error_msg[:2000],  # Cap error size
            }
    
    def chat(
        self,
        messages: List[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Simple chat interface that uses RLM for knowledge queries.
        
        If the query seems to need knowledge base access, uses RLM.
        Otherwise, passes through to LLM directly.
        """
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Check if this needs knowledge base access
        knowledge_indicators = [
            "document", "file", "knowledge", "based on",
            "according to", "what does", "find", "search",
            "look up", "check", "in the", "from the",
        ]
        
        needs_knowledge = any(
            indicator in user_message.lower()
            for indicator in knowledge_indicators
        )
        
        if needs_knowledge:
            # Use RLM
            result = self.run(user_message)
            return result.answer
        else:
            # Direct LLM call
            return self.llm_call_fn(messages, **kwargs)
