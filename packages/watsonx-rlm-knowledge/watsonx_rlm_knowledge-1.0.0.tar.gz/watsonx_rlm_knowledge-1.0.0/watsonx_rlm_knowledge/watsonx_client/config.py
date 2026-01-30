"""Configuration management for WatsonX client."""

import os
import json
import stat
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


CREDENTIALS_FILE = Path.home() / ".rlm_knowledge" / "watsonx_credentials.json"
DEFAULT_MODEL = "openai/gpt-oss-120b"
DEFAULT_REGION_URL = "https://us-south.ml.cloud.ibm.com"


@dataclass
class WatsonXConfig:
    """Configuration for WatsonX client.

    Can be initialized directly or loaded from credentials file.

    Attributes:
        api_key: IBM Cloud API key
        project_id: WatsonX project ID
        region_url: WatsonX region URL (e.g., https://us-south.ml.cloud.ibm.com)
        model_id: Default model to use (defaults to openai/gpt-oss-120b)
        max_retries: Maximum retry attempts for tool/JSON extraction
        timeout: Request timeout in seconds
    """
    api_key: str = ""
    project_id: str = ""
    region_url: str = DEFAULT_REGION_URL
    model_id: str = DEFAULT_MODEL
    max_retries: int = 3
    timeout: int = 120

    # Generation parameters
    max_tokens: int = 8192  # High default to avoid thinking-only truncation
    temperature: float = 0.1  # Lower for more consistent output
    top_p: float = 1.0
    repetition_penalty: float = 1.0

    # Reasoning control (for gpt-oss models)
    # Options: "low", "medium", "high" - "low" minimizes thinking output
    reasoning_effort: str = "low"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.region_url:
            self.region_url = DEFAULT_REGION_URL
        if not self.model_id:
            self.model_id = DEFAULT_MODEL

    @classmethod
    def from_env(cls) -> "WatsonXConfig":
        """Create config from environment variables.

        Environment variables:
            WATSONX_API_KEY: IBM Cloud API key
            WATSONX_PROJECT_ID: WatsonX project ID
            WATSONX_REGION_URL: WatsonX region URL
            WATSONX_MODEL_ID: Default model ID
        """
        return cls(
            api_key=os.environ.get("WATSONX_API_KEY", ""),
            project_id=os.environ.get("WATSONX_PROJECT_ID", ""),
            region_url=os.environ.get("WATSONX_REGION_URL", DEFAULT_REGION_URL),
            model_id=os.environ.get("WATSONX_MODEL_ID", DEFAULT_MODEL),
            max_retries=int(os.environ.get("WATSONX_MAX_RETRIES", "3")),
            timeout=int(os.environ.get("WATSONX_TIMEOUT", "120")),
        )

    @classmethod
    def from_file(cls, filepath: Optional[Path] = None) -> "WatsonXConfig":
        """Load config from credentials file.

        Args:
            filepath: Path to credentials JSON file (default: ~/.rlm_knowledge/watsonx_credentials.json)
        """
        filepath = filepath or CREDENTIALS_FILE

        if not filepath.exists():
            raise FileNotFoundError(f"Credentials file not found: {filepath}")

        with open(filepath, "r") as f:
            data = json.load(f)

        return cls(
            api_key=data.get("api_key", ""),
            project_id=data.get("project_id", ""),
            region_url=data.get("region_url", DEFAULT_REGION_URL),
            model_id=data.get("model_id", DEFAULT_MODEL),
        )

    def save_to_file(self, filepath: Optional[Path] = None) -> None:
        """Save config to credentials file with secure permissions.

        Args:
            filepath: Path to save credentials (default: ~/.rlm_knowledge/watsonx_credentials.json)
        """
        filepath = filepath or CREDENTIALS_FILE

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "api_key": self.api_key,
            "project_id": self.project_id,
            "region_url": self.region_url,
            "model_id": self.model_id,
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        # Set file permissions to owner read/write only (600)
        os.chmod(filepath, stat.S_IRUSR | stat.S_IWUSR)

    def validate(self) -> bool:
        """Check if config has required fields."""
        return bool(self.api_key and self.project_id and self.region_url)

    @property
    def credentials(self) -> Dict[str, str]:
        """Get credentials dict for IBM SDK."""
        return {
            "url": self.region_url,
            "apikey": self.api_key,
        }

    def get_generation_params(self) -> Dict[str, Any]:
        """Get default generation parameters.

        Note: The API uses 'max_tokens' (not 'max_new_tokens').
        top_k is not supported by this model.
        """
        params = {
            "max_tokens": self.max_tokens,  # API uses max_tokens, not max_new_tokens
            "temperature": self.temperature,
            "top_p": self.top_p,
            "repetition_penalty": self.repetition_penalty,
        }
        # reasoning_effort controls how much "thinking" the model does
        if self.reasoning_effort:
            params["reasoning_effort"] = self.reasoning_effort
        return params
