"""Context guard for monitoring token usage and triggering rotations."""

from typing import Optional


class ContextGuard:
    """Monitors token usage and triggers context rotation at threshold."""

    def __init__(self, threshold_percentage: float = 10.0, max_context: int = 1000000):
        """Initialize the context guard.

        Args:
            threshold_percentage: Percentage of max_context to trigger rotation (default 10%)
            max_context: Maximum context window size in tokens (Nemotron-3-Nano: 1M tokens!)
        """
        self.threshold_percentage = threshold_percentage
        self.max_context = max_context
        self.threshold_tokens = int(max_context * (threshold_percentage / 100.0))
        self.current_tokens = 0

    def add_tokens(self, token_count: int):
        """Add tokens to the current count."""
        self.current_tokens += token_count

    def should_rotate(self) -> bool:
        """Check if context should be rotated."""
        return self.current_tokens >= self.threshold_tokens

    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of threshold."""
        return (self.current_tokens / self.threshold_tokens) * 100.0

    def reset(self):
        """Reset token counter (after rotation)."""
        self.current_tokens = 0

    def get_status(self) -> dict:
        """Get current status."""
        return {
            "current_tokens": self.current_tokens,
            "threshold_tokens": self.threshold_tokens,
            "threshold_percentage": self.threshold_percentage,
            "usage_percentage": self.get_usage_percentage(),
            "should_rotate": self.should_rotate()
        }
