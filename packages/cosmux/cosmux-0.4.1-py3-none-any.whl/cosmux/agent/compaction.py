"""
Context Compaction for Cosmux

This module handles automatic context management when conversations exceed token limits.
Based on opencode's implementation: https://github.com/sst/opencode

The compaction process:
1. Token counting - Estimate tokens from message content
2. Overflow detection - Check if context exceeds model limits
3. Tool output pruning - Remove old tool outputs to save tokens
4. Conversation summarization - Summarize old messages when pruning isn't enough
"""

import json
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# Token estimation (same as opencode)
CHARS_PER_TOKEN = 4

# Pruning thresholds (from opencode)
PRUNE_MINIMUM = 20_000  # Minimum tokens to prune
PRUNE_PROTECT = 40_000  # Protect last N tokens of tool calls from pruning

# Default context limits (Claude Opus 4.5)
DEFAULT_CONTEXT_LIMIT = 200_000  # Claude Opus 4.5 context window
DEFAULT_OUTPUT_LIMIT = 64_000  # Claude Opus 4.5 max output tokens


@dataclass
class TokenUsage:
    """Token usage tracking for a message or session"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cache_write: int = 0

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens + self.cache_read


@dataclass
class CompactionResult:
    """Result of a compaction operation"""
    compacted: bool = False
    pruned_count: int = 0
    pruned_tokens: int = 0
    summary: Optional[str] = None
    new_messages: list = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count from text.

    Uses simple character-based estimation (4 chars per token).
    This is the same approach used by opencode.

    Args:
        text: The text to estimate tokens for

    Returns:
        Estimated token count
    """
    if not text:
        return 0
    return max(0, round(len(text) / CHARS_PER_TOKEN))


def estimate_message_tokens(message: dict) -> int:
    """
    Estimate tokens for a single message.

    Args:
        message: Message dict with 'role' and 'content'

    Returns:
        Estimated token count
    """
    content = message.get("content", "")

    if isinstance(content, str):
        return estimate_tokens(content)
    elif isinstance(content, list):
        # Handle structured content (tool results, etc.)
        total = 0
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    total += estimate_tokens(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    total += estimate_tokens(str(block.get("content", "")))
                elif block.get("type") == "tool_use":
                    total += estimate_tokens(json.dumps(block.get("input", {})))
                else:
                    total += estimate_tokens(json.dumps(block))
            elif isinstance(block, str):
                total += estimate_tokens(block)
        return total

    return estimate_tokens(str(content))


def estimate_conversation_tokens(messages: list[dict]) -> int:
    """
    Estimate total tokens for a conversation.

    Args:
        messages: List of message dicts

    Returns:
        Total estimated token count
    """
    return sum(estimate_message_tokens(msg) for msg in messages)


def is_overflow(
    token_usage: TokenUsage,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> bool:
    """
    Check if context has overflowed the model's limits.

    Args:
        token_usage: Current token usage
        context_limit: Model's context window size
        output_limit: Max output tokens reserved

    Returns:
        True if overflow detected
    """
    if context_limit == 0:
        return False

    usable = context_limit - output_limit
    return token_usage.total > usable


def should_compact(
    messages: list[dict],
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
    threshold: float = 0.8,
) -> bool:
    """
    Check if compaction should be triggered.

    Args:
        messages: Conversation messages
        context_limit: Model's context window size
        output_limit: Max output tokens reserved
        threshold: Trigger compaction at this % of context usage

    Returns:
        True if compaction should be triggered
    """
    total_tokens = estimate_conversation_tokens(messages)
    usable = context_limit - output_limit
    return total_tokens > (usable * threshold)


def prune_tool_outputs(
    messages: list[dict],
    protect_tokens: int = PRUNE_PROTECT,
    minimum_prune: int = PRUNE_MINIMUM,
) -> tuple[list[dict], int]:
    """
    Prune old tool outputs to reduce context size.

    Goes backwards through messages and marks old tool outputs
    for pruning once we've protected the most recent N tokens.

    Args:
        messages: Conversation messages
        protect_tokens: Protect the last N tokens of tool outputs
        minimum_prune: Only prune if we can save at least this many tokens

    Returns:
        Tuple of (pruned messages, tokens saved)
    """
    pruned_messages = []
    total_tool_tokens = 0
    tokens_to_prune = 0
    tool_outputs_to_prune = []

    # First pass: identify tool outputs and their token counts
    for i, msg in enumerate(reversed(messages)):
        msg_copy = msg.copy()
        content = msg_copy.get("content")

        if isinstance(content, list):
            new_content = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    output = str(block.get("content", ""))
                    tokens = estimate_tokens(output)
                    total_tool_tokens += tokens

                    # If we've seen enough tokens, mark for pruning
                    if total_tool_tokens > protect_tokens:
                        tokens_to_prune += tokens
                        tool_outputs_to_prune.append((len(messages) - 1 - i, len(new_content)))
                        # Mark as pruned
                        pruned_block = block.copy()
                        pruned_block["content"] = "[TOOL OUTPUT PRUNED - Context compaction]"
                        pruned_block["_pruned"] = True
                        pruned_block["_original_tokens"] = tokens
                        new_content.append(pruned_block)
                    else:
                        new_content.append(block)
                else:
                    new_content.append(block)
            msg_copy["content"] = new_content
        pruned_messages.insert(0, msg_copy)

    # Only apply pruning if we meet the minimum threshold
    if tokens_to_prune >= minimum_prune:
        return pruned_messages, tokens_to_prune
    else:
        # Return original messages if pruning threshold not met
        return messages, 0


# Compaction prompt (from opencode)
COMPACTION_SYSTEM_PROMPT = """You are a helpful AI assistant tasked with summarizing conversations.

When asked to summarize, provide a detailed but concise summary of the conversation.
Focus on information that would be helpful for continuing the conversation, including:
- What was done
- What is currently being worked on
- Which files are being modified
- What needs to be done next
- Key user requests, constraints, or preferences that should persist
- Important technical decisions and why they were made

Your summary should be comprehensive enough to provide context but concise enough to be quickly understood."""

COMPACTION_USER_PROMPT = """Provide a detailed prompt for continuing our conversation above. Focus on information that would be helpful for continuing the conversation, including what we did, what we're doing, which files we're working on, and what we're going to do next considering a new session will not have access to our conversation.

Start your summary with: "This session is being continued from a previous conversation that ran out of context. Here's what happened:"
"""


async def create_summary(
    messages: list[dict],
    summarize_fn,
) -> Optional[str]:
    """
    Create a summary of the conversation using an LLM.

    Args:
        messages: Messages to summarize
        summarize_fn: Async function to call LLM for summarization
                     Should accept (system_prompt, messages) and return text

    Returns:
        Summary text or None if summarization failed
    """
    try:
        # Prepare messages for summarization
        summary_messages = messages + [
            {"role": "user", "content": COMPACTION_USER_PROMPT}
        ]

        summary = await summarize_fn(COMPACTION_SYSTEM_PROMPT, summary_messages)
        return summary
    except Exception as e:
        print(f"[Compaction] Failed to create summary: {e}")
        return None


async def compact_conversation(
    messages: list[dict],
    summarize_fn,
    context_limit: int = DEFAULT_CONTEXT_LIMIT,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> CompactionResult:
    """
    Perform full context compaction on a conversation.

    This is the main entry point for compaction. It will:
    1. Check if compaction is needed
    2. Try pruning tool outputs first
    3. If still over limit, create a summary

    Args:
        messages: Conversation messages
        summarize_fn: Async function to call LLM for summarization
        context_limit: Model's context window size
        output_limit: Max output tokens reserved

    Returns:
        CompactionResult with details of what was done
    """
    result = CompactionResult()

    # Check if we need to compact
    if not should_compact(messages, context_limit, output_limit):
        return result

    print(f"[Compaction] Starting compaction - {estimate_conversation_tokens(messages)} tokens")

    # Step 1: Try pruning tool outputs
    pruned_messages, pruned_tokens = prune_tool_outputs(messages)
    if pruned_tokens > 0:
        result.pruned_tokens = pruned_tokens
        result.pruned_count = sum(
            1 for msg in pruned_messages
            if isinstance(msg.get("content"), list)
            for block in msg["content"]
            if isinstance(block, dict) and block.get("_pruned")
        )
        print(f"[Compaction] Pruned {result.pruned_count} tool outputs ({pruned_tokens} tokens)")

    # Check if pruning was enough
    if not should_compact(pruned_messages, context_limit, output_limit):
        result.compacted = True
        result.new_messages = pruned_messages
        return result

    # Step 2: Create summary if still over limit
    print("[Compaction] Pruning not sufficient, creating summary...")
    summary = await create_summary(pruned_messages, summarize_fn)

    if summary:
        result.summary = summary
        result.compacted = True

        # Create new message list with summary
        result.new_messages = [
            {
                "role": "user",
                "content": summary,
            },
            {
                "role": "assistant",
                "content": "I understand. I'll continue from where we left off based on this context. What would you like me to do next?",
            },
        ]
        print(f"[Compaction] Created summary ({estimate_tokens(summary)} tokens)")
    else:
        # Fallback: just use pruned messages
        result.new_messages = pruned_messages

    return result


class CompactionManager:
    """
    Manages context compaction for a session.

    Tracks token usage and triggers compaction when needed.
    """

    def __init__(
        self,
        context_limit: int = DEFAULT_CONTEXT_LIMIT,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
        threshold: float = 0.8,
    ):
        self.context_limit = context_limit
        self.output_limit = output_limit
        self.threshold = threshold
        self.last_compaction: Optional[datetime] = None
        self.compaction_count = 0

    def check_and_compact(
        self,
        messages: list[dict],
    ) -> bool:
        """
        Check if compaction is needed.

        Args:
            messages: Current conversation messages

        Returns:
            True if compaction should be triggered
        """
        return should_compact(
            messages,
            self.context_limit,
            self.output_limit,
            self.threshold,
        )

    async def compact(
        self,
        messages: list[dict],
        summarize_fn,
    ) -> CompactionResult:
        """
        Perform compaction.

        Args:
            messages: Current conversation messages
            summarize_fn: Function to create summaries

        Returns:
            CompactionResult
        """
        result = await compact_conversation(
            messages,
            summarize_fn,
            self.context_limit,
            self.output_limit,
        )

        if result.compacted:
            self.last_compaction = datetime.now()
            self.compaction_count += 1

        return result

    def get_stats(self) -> dict:
        """Get compaction statistics."""
        return {
            "compaction_count": self.compaction_count,
            "last_compaction": self.last_compaction.isoformat() if self.last_compaction else None,
            "context_limit": self.context_limit,
            "output_limit": self.output_limit,
            "threshold": self.threshold,
        }
