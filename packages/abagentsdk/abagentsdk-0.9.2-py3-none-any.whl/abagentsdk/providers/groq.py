# abagent/providers/groq.py
from __future__ import annotations
import os as _os

from groq import Groq
from typing import Optional

from .base import ModelProvider
from ..config import SDKConfig


class GroqProvider(ModelProvider):
    """
    Wrapper around Groq API. Requires a user-supplied API key.
    """

    def __init__(self, config: SDKConfig):
        self.config = config.require_key()  # enforce key
        
        # Initialize Groq client
        self.client = Groq(
            api_key=self.config.api_key
        )
        self._model_name = self.config.model

    @property
    def model(self) -> str:
        return self._model_name

    def generate(self, prompt: str) -> str:
        """
        Generate content using Groq's chat completions API.
        """
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self._model_name,
            )
            
            # Extract the response content
            return chat_completion.choices[0].message.content or ""
        except Exception as e:
            return f"[Groq Error] {str(e)}"
