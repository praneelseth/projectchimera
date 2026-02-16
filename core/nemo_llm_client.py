"""NeMo Agent Toolkit LLM client wrapper for NVIDIA Nemotron."""

import os
from typing import Optional
from openai import OpenAI


class NeMoLLMClient:
    """LLM client using NVIDIA NIM with Nemotron-3-Nano-30B-A3B.

    Uses OpenAI-compatible API format for NVIDIA's API endpoint.
    """

    def __init__(self, model: str = "nvidia/nemotron-3-nano-30b-a3b", api_key: Optional[str] = None):
        """Initialize the NeMo LLM client.

        Args:
            model: NVIDIA model identifier
            api_key: NVIDIA API key (defaults to NVIDIA_API_KEY env var)
        """
        self.model = model
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")

        if not self.api_key:
            raise ValueError("NVIDIA_API_KEY not found in environment")

        # Initialize OpenAI client pointing to NVIDIA endpoint
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key
        )

        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def chat(self, messages: list, max_tokens: int = 4096, temperature: float = 0.3) -> dict:
        """Send a chat request to Nemotron.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dict with response content and token usage
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        # Track token usage
        if hasattr(response, 'usage'):
            self.total_input_tokens += response.usage.prompt_tokens
            self.total_output_tokens += response.usage.completion_tokens

        # Extract response
        content = response.choices[0].message.content

        return {
            "content": content,
            "input_tokens": response.usage.prompt_tokens if hasattr(response, 'usage') else 0,
            "output_tokens": response.usage.completion_tokens if hasattr(response, 'usage') else 0
        }

    def get_total_tokens(self) -> int:
        """Get total tokens used in this session."""
        return self.total_input_tokens + self.total_output_tokens

    def reset_token_count(self):
        """Reset token counters (for context rotation)."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def get_client(self):
        """Get the underlying OpenAI client for NAT integration."""
        return self.client
