"""LLM client abstraction for Claude API with tool calling support."""

import os
from typing import Dict, List, Optional, Any
from anthropic import Anthropic


class LLMClient:
    """Unified interface for LLM interactions with token tracking and tool support."""

    def __init__(self, model: str = "claude-sonnet-4-5-20250929", api_key: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            model: Model identifier
            api_key: API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.model = model
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def chat(self, system_prompt: str, messages: List[Dict[str, Any]],
             max_tokens: int = 8000, tools: Optional[List[Dict]] = None) -> Dict:
        """Send a chat request to the LLM.

        Args:
            system_prompt: System prompt to guide behavior
            messages: List of message dicts (user/assistant messages)
            max_tokens: Maximum tokens in response
            tools: Optional list of tool definitions for function calling

        Returns:
            Dict with:
                - content: Response text (if no tool use)
                - tool_uses: List of tool use requests (if tools used)
                - input_tokens: Tokens in request
                - output_tokens: Tokens in response
                - stop_reason: Why generation stopped
        """
        params = {
            "model": self.model,
            "system": system_prompt,
            "messages": messages,
            "max_tokens": max_tokens
        }

        if tools:
            params["tools"] = tools

        response = self.client.messages.create(**params)

        # Extract token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Accumulate totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        # Extract content
        content_text = ""
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_uses.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return {
            "content": content_text,
            "tool_uses": tool_uses,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "stop_reason": response.stop_reason
        }

    def get_total_tokens(self) -> int:
        """Get total tokens used in this session."""
        return self.total_input_tokens + self.total_output_tokens

    def reset_token_count(self):
        """Reset token counters (for context rotation)."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
