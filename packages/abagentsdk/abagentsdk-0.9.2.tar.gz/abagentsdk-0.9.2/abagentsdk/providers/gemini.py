import os as _os

# extra guard in case this file is imported directly
_os.environ.setdefault("GRPC_VERBOSITY", "ERROR")
_os.environ.setdefault("GRPC_LOG_SEVERITY_OVERRIDE", "ERROR")
_os.environ.setdefault("ABSL_LOGGING_STDERR_THRESHOLD", "3")
_os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

from google import genai
from typing import Optional

from .base import ModelProvider
from ..config import SDKConfig


class GeminiProvider(ModelProvider):
    """
    Wrapper around google-genai (new SDK). Requires a user-supplied API key.
    """

    def __init__(self, config: SDKConfig):
        self.config = config.require_key()  # enforce key
        self.client = genai.Client(api_key=self.config.api_key)
        self._model_name = self.config.model

    @property
    def model(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        resp = self.client.models.generate_content(
            model=self._model_name,
            contents=prompt
        )
        return getattr(resp, "text", "") or ""
