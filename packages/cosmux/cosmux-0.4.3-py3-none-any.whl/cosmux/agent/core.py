"""Agent orchestrator - Claude SDK integration with direct HTTP for OAuth"""

import asyncio
import json
import os
from pathlib import Path
from typing import AsyncGenerator, Any, Callable, Awaitable, Optional

import httpx
from anthropic import AsyncAnthropic

from cosmux.agent.context import load_project_context, build_system_prompt
from cosmux.agent.compaction import (
    CompactionManager,
    estimate_conversation_tokens,
    COMPACTION_SYSTEM_PROMPT,
)
from cosmux.auth.credentials import (
    AuthResult,
    get_credentials,
    is_token_expired,
    refresh_oauth_token,
    save_credentials,
)
from cosmux.config import settings
from cosmux.db.repository import SessionRepository
from cosmux.tools import (
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    BashTool,
    AskUserQuestionTool,
    ToolRegistry,
)


# Anthropic API configuration for direct HTTP calls
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# OAuth beta headers required for Claude Max subscription
# Source: opencode-anthropic-auth plugin
OAUTH_BETA_HEADERS = ",".join([
    "oauth-2025-04-20",
    "claude-code-20250219",
    "interleaved-thinking-2025-05-14",
    "fine-grained-tool-streaming-2025-05-14",
])

# Claude Code identity for OAuth (CRITICAL!)
# Source: https://github.com/sst/opencode/blob/dev/packages/opencode/src/session/prompt/anthropic_spoof.txt
CLAUDE_CODE_SPOOF = "You are Claude Code, Anthropic's official CLI for Claude."


# Tools that are blocked in plan mode (write operations)
PLAN_MODE_BLOCKED_TOOLS = {"Write", "Edit", "Bash"}


class AgentOrchestrator:
    """
    Orchestrates the Claude agent with tools and streaming.
    """

    def __init__(
        self,
        workspace_path: str,
        session_id: str,
        db: Any,
    ):
        self.workspace_path = Path(workspace_path).resolve()
        self.session_id = session_id
        self.db = db

        # Plan mode flag
        self.plan_mode = False
        self._base_system_prompt = ""

        # Load project context
        self.context = load_project_context(self.workspace_path)

        # Build system prompt
        self._base_system_prompt = build_system_prompt(self.context, self.workspace_path)
        self.system_prompt = self._base_system_prompt

        # Initialize authentication
        self._auth: Optional[AuthResult] = None
        self._init_auth()

        # Initialize tools
        self.tool_registry = ToolRegistry()
        self._register_tools()

        # Pending user responses for AskUserQuestion tool
        self._pending_responses: dict[str, asyncio.Future] = {}

        # Event sender callback (set by websocket handler)
        self._send_event: Callable[[dict], Awaitable[None]] | None = None

        # Context compaction manager
        # Handles automatic summarization when context exceeds limits
        self._compaction_manager = CompactionManager(
            context_limit=200_000,  # Claude Opus 4.5 context window
            output_limit=settings.max_tokens,  # 64k for Opus 4.5
            threshold=0.75,  # Compact at 75% usage
        )

    def set_event_sender(self, sender: Callable[[dict], Awaitable[None]]) -> None:
        """Set the callback for sending events to the client"""
        self._send_event = sender

    def _init_auth(self) -> None:
        """Initialize authentication from available credential sources"""
        self._auth = get_credentials()
        if not self._auth:
            raise ValueError(
                "No API credentials found. Options:\n"
                "1. Run 'cosmux login' for Claude Max subscription, or\n"
                "2. Set ANTHROPIC_API_KEY for pay-per-token API"
            )

        # For OAuth authentication, we send Claude Code identity as SEPARATE block
        # This is CRITICAL for OAuth to work!
        # The API checks the first system block to verify the client is Claude Code
        self._use_oauth = self._auth.source != "api_key"
        if self._use_oauth:
            # DON'T modify _base_system_prompt - we'll add the spoof as separate block in the request
            print(f"[DEBUG] Auth source: {self._auth.source}")
            print(f"[DEBUG] Using OAuth mode with direct HTTP")
            # For OAuth, we use direct httpx instead of SDK
            self._http_client = httpx.AsyncClient(timeout=300.0)
            self.client = None  # Not used for OAuth
        else:
            # Standard API key - use SDK
            self._http_client = None
            self.client = AsyncAnthropic(api_key=self._auth.token)

    def _get_oauth_headers(self) -> dict[str, str]:
        """Get headers for OAuth requests (like opencode's custom fetch)"""
        # User-Agent like opencode/Claude Code
        # Source: opencode uses "opencode/{channel}/{version}/{client}"
        # The AI SDK also adds user-agent suffix
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._auth.token}",
            "anthropic-version": ANTHROPIC_VERSION,
            "anthropic-beta": OAUTH_BETA_HEADERS,
            "User-Agent": "claude-code/1.0.0 ai-sdk/anthropic/3.0.9",
            # NO x-api-key header - this is critical!
        }

    async def _ensure_valid_token(self) -> None:
        """Check and refresh OAuth token if needed (before each API call)"""
        if not self._auth or self._auth.source == "api_key":
            return  # API keys don't expire

        # Check if token is expired or will expire soon
        if is_token_expired(self._auth.expires_at):
            if self._auth.refresh_token:
                print("[Info] OAuth token expired, refreshing...")
                new_auth = await refresh_oauth_token(self._auth.refresh_token)
                if new_auth:
                    self._auth = new_auth
                    # Save refreshed credentials
                    save_credentials({
                        "accessToken": new_auth.token,
                        "refreshToken": new_auth.refresh_token or "",
                        "expiresAt": new_auth.expires_at or 0,
                    })
                    print("[Info] OAuth token refreshed successfully")
                else:
                    print("[Warning] Failed to refresh token, using existing")

    async def _stream_oauth_response(
        self,
        messages: list[dict],
        system_prompt: str,
        _retry_on_revoked: bool = True,
        enable_thinking: bool = True,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream response using direct HTTP for OAuth.

        This replicates opencode's approach exactly:
        - Direct HTTP request to Anthropic API
        - OAuth headers (no x-api-key)
        - SSE streaming response parsing
        - System prompt as SEPARATE blocks (critical for OAuth!)

        Source: opencode-anthropic-auth plugin
        """
        # Build system prompt as SEPARATE blocks like opencode does!
        # Block 1: Claude Code identity (MUST be first and separate!)
        # Block 2: Rest of the system prompt (from self.system_prompt)
        # This is CRITICAL for OAuth to work!
        system_blocks = [
            {"type": "text", "text": CLAUDE_CODE_SPOOF},
            {"type": "text", "text": system_prompt},
        ]

        # Build request payload (Anthropic API format)
        payload = {
            "model": settings.model,
            "max_tokens": settings.max_tokens,
            "system": system_blocks,
            "messages": self._convert_messages_for_api(messages),
            "tools": self._get_tools_schema(),
            "stream": True,
        }

        # Only enable thinking if explicitly requested
        # Note: When thinking is enabled with history, the API requires
        # that previous assistant messages start with thinking blocks.
        # Since we can't reliably preserve thinking signatures across
        # save/load cycles, we disable thinking when there's history.
        if enable_thinking:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": 10000,
            }

        # DEBUG: Log request (with flush for immediate output)
        print(f"[DEBUG OAuth] Request to: {ANTHROPIC_API_URL}", flush=True)
        print(f"[DEBUG OAuth] enable_thinking={enable_thinking}", flush=True)
        print(f"[DEBUG OAuth] Messages count: {len(self._convert_messages_for_api(messages))}", flush=True)
        headers = self._get_oauth_headers()

        async with self._http_client.stream(
            "POST",
            ANTHROPIC_API_URL,
            json=payload,
            headers=headers,
        ) as response:
            # Check for errors
            if response.status_code != 200:
                error_body = await response.aread()
                error_text = error_body.decode("utf-8")
                print(f"[DEBUG OAuth] Error response: {error_text}")

                # Handle revoked/expired token - attempt refresh and retry
                is_token_error = (
                    (response.status_code == 403 and "revoked" in error_text.lower()) or
                    (response.status_code == 401 and "expired" in error_text.lower())
                )
                if is_token_error and _retry_on_revoked:
                    print("[Info] Token revoked, attempting refresh...")
                    if self._auth and self._auth.refresh_token:
                        new_auth = await refresh_oauth_token(self._auth.refresh_token)
                        if new_auth:
                            self._auth = new_auth
                            save_credentials({
                                "accessToken": new_auth.token,
                                "refreshToken": new_auth.refresh_token or "",
                                "expiresAt": new_auth.expires_at or 0,
                            })
                            print("[Info] Token refreshed successfully, retrying request...")
                            # Retry the request with new token (only once)
                            async for event in self._stream_oauth_response(
                                messages, system_prompt, _retry_on_revoked=False
                            ):
                                yield event
                            return
                        else:
                            raise Exception(
                                "OAuth token was revoked and refresh failed. "
                                "Please run 'cosmux login' to re-authenticate."
                            )
                    else:
                        raise Exception(
                            "OAuth token was revoked and no refresh token available. "
                            "Please run 'cosmux login' to re-authenticate."
                        )

                raise Exception(f"Anthropic API error ({response.status_code}): {error_text}")

            # Parse SSE stream
            current_text = ""
            current_thinking = ""
            content_blocks: list[dict] = []
            message_id = ""
            model = ""

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("event: "):
                    event_type = line[7:].strip()
                    continue

                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    event_type = data.get("type", "")

                    if event_type == "message_start":
                        message = data.get("message", {})
                        message_id = message.get("id", "")
                        model = message.get("model", "")

                    elif event_type == "content_block_start":
                        block = data.get("content_block", {})
                        index = data.get("index", 0)
                        while len(content_blocks) <= index:
                            content_blocks.append({})

                        block_type = block.get("type")
                        if block_type == "thinking":
                            # Debug: Log the full thinking block start
                            print(f"[DEBUG] content_block_start thinking: {block}", flush=True)
                            content_blocks[index] = {
                                "type": "thinking",
                                "thinking": "",  # Will be filled by thinking_delta
                            }
                            # Check if signature is already in start block
                            if "signature" in block:
                                content_blocks[index]["signature"] = block["signature"]
                                print(f"[DEBUG] Signature in start block!", flush=True)
                        elif block_type == "text":
                            content_blocks[index] = {
                                "type": "text",
                                "text": "",  # Will be filled by text_delta
                            }
                        else:
                            # tool_use or other types
                            content_blocks[index] = {
                                "type": block_type,
                                "id": block.get("id"),
                                "name": block.get("name"),
                                "input": "",
                            }

                    elif event_type == "content_block_delta":
                        index = data.get("index", 0)
                        delta = data.get("delta", {})

                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            current_text += text
                            # Update the text block in content_blocks
                            if index < len(content_blocks) and content_blocks[index].get("type") == "text":
                                content_blocks[index]["text"] += text
                            yield {
                                "type": "text_delta",
                                "delta": text,
                            }

                        elif delta.get("type") == "thinking_delta":
                            # Extended thinking content (interleaved-thinking beta)
                            thinking_text = delta.get("thinking", "")
                            current_thinking += thinking_text
                            # Update the thinking block in content_blocks
                            if index < len(content_blocks) and content_blocks[index].get("type") == "thinking":
                                content_blocks[index]["thinking"] += thinking_text
                            yield {
                                "type": "thinking",
                                "text": current_thinking,
                            }

                        elif delta.get("type") == "signature_delta":
                            # Signature for thinking block (if sent as delta)
                            signature = delta.get("signature", "")
                            print(f"[DEBUG] signature_delta received: {signature[:50] if signature else 'EMPTY'}...", flush=True)
                            if index < len(content_blocks) and content_blocks[index].get("type") == "thinking":
                                content_blocks[index]["signature"] = content_blocks[index].get("signature", "") + signature

                        elif delta.get("type") == "input_json_delta":
                            # Tool input streaming
                            partial_json = delta.get("partial_json", "")
                            if index < len(content_blocks):
                                content_blocks[index]["input"] += partial_json

                        else:
                            # Log unknown delta types to catch any we might be missing
                            delta_type = delta.get("type", "UNKNOWN")
                            print(f"[DEBUG] Unknown delta type: {delta_type}, delta keys: {delta.keys()}", flush=True)

                    elif event_type == "content_block_stop":
                        index = data.get("index", 0)
                        # Debug: Log the full data object to understand structure
                        print(f"[DEBUG] content_block_stop RAW data: {json.dumps(data)}", flush=True)

                        # Get the content_block from the stop event (contains signature for thinking)
                        stop_block = data.get("content_block", {})

                        if index < len(content_blocks):
                            block = content_blocks[index]
                            if block.get("type") == "tool_use":
                                # Parse the accumulated JSON input
                                try:
                                    block["input"] = json.loads(block["input"]) if block["input"] else {}
                                except json.JSONDecodeError:
                                    block["input"] = {}
                            elif block.get("type") == "thinking":
                                # Check if signature was already set by signature_delta
                                existing_signature = block.get("signature")
                                print(f"[DEBUG] content_block_stop for thinking:", flush=True)
                                print(f"[DEBUG]   existing signature from signature_delta: {'YES' if existing_signature else 'NO'}", flush=True)

                                if not existing_signature:
                                    # Try to get signature from stop event as fallback
                                    signature = stop_block.get("signature") or data.get("signature")
                                    print(f"[DEBUG]   stop_block: {stop_block}", flush=True)
                                    print(f"[DEBUG]   fallback signature from stop event: {signature[:50] if signature else 'NONE'}...", flush=True)
                                    if signature:
                                        block["signature"] = signature
                                    else:
                                        print(f"[DEBUG] WARNING: No signature captured! Thinking block will be incomplete.", flush=True)
                                else:
                                    print(f"[DEBUG]   signature length: {len(existing_signature)}", flush=True)

                    elif event_type == "message_delta":
                        delta = data.get("delta", {})
                        stop_reason = delta.get("stop_reason")
                        if stop_reason:
                            # Yield final message info
                            yield {
                                "type": "_message_complete",
                                "stop_reason": stop_reason,
                                "content_blocks": content_blocks,
                                "text": current_text,
                            }

                    elif event_type == "message_stop":
                        pass

    def _convert_messages_for_api(self, messages: list[dict]) -> list[dict]:
        """Convert messages to Anthropic API format.

        Key behaviors:
        - Thinking blocks from HISTORY are filtered (cannot end with thinking)
        - tool_use and tool_result are KEPT (needed for current turn tool loops)
        - Only text blocks are kept from history assistant messages

        Note: tool_use/tool_result only exist in current turn (not saved to DB),
        so we must keep them for the tool use loop to work correctly.
        """
        result = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")

            if role == "user":
                if isinstance(content, str):
                    result.append({"role": "user", "content": content})
                elif isinstance(content, list):
                    # Keep all user content (including tool_result for current turn)
                    result.append({"role": "user", "content": content})
                else:
                    result.append({"role": "user", "content": str(content)})

            elif role == "assistant":
                if isinstance(content, str):
                    result.append({
                        "role": "assistant",
                        "content": [{"type": "text", "text": content}]
                    })
                elif isinstance(content, list):
                    # Check if this is a current-turn message (has tool_use) or history
                    has_tool_use = any(b.get("type") == "tool_use" for b in content)

                    if has_tool_use:
                        # Current turn with tool use - keep everything (including thinking)
                        # This is required for the tool use loop to work
                        result.append({"role": "assistant", "content": content})
                    else:
                        # History message - filter out thinking blocks
                        # (they cause "message cannot end with thinking" error)
                        filtered_content = [
                            block for block in content
                            if block.get("type") != "thinking"
                        ]
                        if filtered_content:
                            result.append({"role": "assistant", "content": filtered_content})
                else:
                    result.append({"role": "assistant", "content": content})

        return result

    def set_plan_mode(self, enabled: bool) -> None:
        """Enable or disable plan mode"""
        self.plan_mode = enabled
        self._update_system_prompt()

    def _update_system_prompt(self) -> None:
        """Update system prompt based on plan mode"""
        if self.plan_mode:
            self.system_prompt = self._base_system_prompt + """

## PLAN MODE ACTIVE

You are in **plan mode**. You MUST NOT execute any write operations.

**Restrictions:**
- DO NOT use Write, Edit, or Bash tools - they will be blocked
- You MAY use Read, Glob, Grep for research and exploration

**Your task in plan mode:**
1. Research the codebase to understand the current state
2. Create a detailed implementation plan
3. Use AskUserQuestion to present your plan and get approval
4. Once approved, the user will switch to Implementation Mode

**Plan format:**
- List specific files to create or modify
- Describe the changes in each file
- Explain the implementation approach
- Note any potential issues or alternatives
"""
        else:
            self.system_prompt = self._base_system_prompt

    def _register_tools(self) -> None:
        """Register all available tools"""
        tools = [
            ReadTool(),
            WriteTool(),
            EditTool(),
            GlobTool(),
            GrepTool(),
            BashTool(),
            AskUserQuestionTool(),
        ]
        for tool in tools:
            self.tool_registry.register(tool)

    def _get_tools_schema(self) -> list[dict]:
        """Get tool schemas for Claude API"""
        return self.tool_registry.get_schemas()

    async def _create_summary(self, system_prompt: str, messages: list[dict]) -> str:
        """
        Create a conversation summary using the LLM.

        This is used by the compaction manager to summarize old conversations.

        Args:
            system_prompt: System prompt for summarization
            messages: Messages to summarize

        Returns:
            Summary text
        """
        # Use a simpler, non-streaming call for summarization
        if self._use_oauth:
            # OAuth mode: Direct HTTP
            payload = {
                "model": settings.model,
                "max_tokens": 4096,  # Summary should be concise
                "system": [
                    {"type": "text", "text": CLAUDE_CODE_SPOOF},
                    {"type": "text", "text": system_prompt},
                ],
                "messages": self._convert_messages_for_api(messages),
                "stream": False,
            }

            headers = self._get_oauth_headers()
            response = await self._http_client.post(
                ANTHROPIC_API_URL,
                json=payload,
                headers=headers,
            )
            if response.status_code != 200:
                raise Exception(f"Summary API error: {response.text}")
            data = response.json()
            # Extract text from response
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block.get("text", "")
            return ""
        else:
            # SDK mode
            response = await self.client.messages.create(
                model=settings.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
            )
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

    async def _check_and_compact(
        self,
        messages: list[dict],
        repo: SessionRepository,
    ) -> list[dict]:
        """
        Check if compaction is needed and perform it if necessary.

        Args:
            messages: Current conversation messages
            repo: Session repository

        Returns:
            Possibly compacted messages
        """
        if not self._compaction_manager.check_and_compact(messages):
            return messages

        # Log context usage
        total_tokens = estimate_conversation_tokens(messages)
        print(f"[Compaction] Context at {total_tokens} tokens, triggering compaction...")

        # Notify client that compaction is happening
        if self._send_event:
            await self._send_event({
                "type": "compaction_start",
                "message": "Summarizing conversation to free up context...",
                "tokens": total_tokens,
            })

        # Perform compaction
        result = await self._compaction_manager.compact(
            messages,
            self._create_summary,
        )

        if result.compacted:
            # Notify client
            if self._send_event:
                await self._send_event({
                    "type": "compaction_complete",
                    "pruned_count": result.pruned_count,
                    "pruned_tokens": result.pruned_tokens,
                    "has_summary": result.summary is not None,
                })

            # If we created a summary, save it to the DB as a system message
            if result.summary:
                # Clear old messages and save summary
                repo.clear_messages(self.session_id)
                repo.add_message(self.session_id, "user", result.summary)
                repo.add_message(
                    self.session_id,
                    "assistant",
                    "I understand. I'll continue from where we left off based on this context."
                )

            return result.new_messages

        return messages

    async def receive_user_response(self, tool_id: str, answers: dict) -> None:
        """Receive user response for a pending AskUserQuestion"""
        if tool_id in self._pending_responses:
            future = self._pending_responses[tool_id]
            if not future.done():
                future.set_result(answers)

    async def stream_response(
        self,
        user_message: str,
        repo: SessionRepository,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Stream agent response with tool use handling.

        Yields events:
        - text_delta: Streaming text content
        - thinking: Extended thinking content
        - tool_start: Tool call started
        - tool_end: Tool call completed
        - question_prompt: Interactive question for user
        - complete: Final message
        - error: Error occurred
        """
        print(f"[DEBUG stream_response] Starting for session {self.session_id}, user_message: {user_message[:50]}...", flush=True)

        # Get conversation history (before adding new message)
        history = repo.get_message_history(self.session_id)

        # Save user message to DB (after getting history to avoid duplication)
        repo.add_message(self.session_id, "user", user_message)

        # Add user message to messages for Claude
        messages = history + [{"role": "user", "content": user_message}]

        try:
            # Ensure OAuth token is still valid before API call
            await self._ensure_valid_token()

            # Check if context compaction is needed
            messages = await self._check_and_compact(messages, repo)

            if self._use_oauth:
                # OAuth mode: Direct HTTP streaming with content blocks
                async for event in self._stream_with_oauth(messages, repo):
                    yield event
            else:
                # SDK mode: Use Anthropic SDK
                async for event in self._stream_with_sdk(messages, repo):
                    yield event

        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
            }

    def _build_assistant_content(self, content_blocks: list, current_text: str) -> list[dict]:
        """Build assistant content blocks for API continuation."""
        assistant_content = []
        for block in content_blocks:
            block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

            if block_type == "text":
                assistant_content.append({"type": "text", "text": current_text})
            elif block_type == "tool_use":
                if isinstance(block, dict):
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "input": block.get("input", {}),
                    })
                else:
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
        return assistant_content

    async def _stream_with_oauth(
        self,
        messages: list[dict],
        repo: SessionRepository,
        accumulated_content: list | None = None,
        is_continuation: bool = False,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream response using OAuth (direct HTTP)"""
        current_text = ""
        stop_reason = None
        content_blocks = []

        # Track accumulated content blocks across continuations
        if accumulated_content is None:
            accumulated_content = []

        # Determine if we should enable thinking
        # With interleaved thinking support, we can enable thinking for all requests.
        # The API handles:
        # - Stripping thinking blocks from previous turns automatically
        # - Validating thinking blocks for the current turn only
        #
        # For tool continuations, interleaved thinking allows Claude to think
        # between tool calls, which improves reasoning quality.
        enable_thinking = True

        # Debug logging
        print(f"[DEBUG Thinking] is_continuation={is_continuation}, enable_thinking={enable_thinking}", flush=True)

        async for event in self._stream_oauth_response(
            messages, self.system_prompt, enable_thinking=enable_thinking
        ):
            if event["type"] == "text_delta":
                current_text += event["delta"]
                yield event
            elif event["type"] == "thinking":
                # Pass through thinking events to frontend
                yield event
            elif event["type"] == "_message_complete":
                stop_reason = event["stop_reason"]
                content_blocks = event["content_blocks"]

        # Process tool uses if any
        if stop_reason == "tool_use":
            tool_results = []
            async for event, results in self._process_tool_uses(content_blocks):
                yield event
                tool_results = results

            # Continue conversation with tool results
            if tool_results:
                # Build assistant content from content_blocks (includes thinking)
                assistant_content = content_blocks  # Use full blocks
                continued_messages = messages + [
                    {"role": "assistant", "content": assistant_content},
                    {"role": "user", "content": tool_results},
                ]

                # Accumulate content blocks for final save
                new_accumulated = accumulated_content + content_blocks

                # Add line break between continuations
                if current_text and not current_text.endswith("\n"):
                    yield {"type": "text_delta", "delta": "\n\n"}

                # Tool continuation - disable thinking for the follow-up request
                async for event in self._stream_with_oauth(
                    continued_messages, repo, new_accumulated, is_continuation=True
                ):
                    yield event
        else:
            # No tool use, save and complete
            # Combine accumulated content with final content blocks
            final_content = accumulated_content + content_blocks

            # Filter out tool_use blocks - they've been executed and including them
            # would require tool_result blocks in the next message (API requirement)
            # We only keep thinking and text blocks for history
            saveable_content = [
                block for block in final_content
                if block.get("type") in ("thinking", "text")
            ]

            # Extract text for display
            final_text = ""
            for block in final_content:
                if block.get("type") == "text":
                    final_text += block.get("text", "")

            if saveable_content:
                # Log what we're about to save
                thinking_blocks = [b for b in saveable_content if b.get("type") == "thinking"]
                text_blocks = [b for b in saveable_content if b.get("type") == "text"]
                print(f"[DEBUG Save] Saving {len(saveable_content)} blocks to DB: {len(thinking_blocks)} thinking, {len(text_blocks)} text", flush=True)
                for tb in thinking_blocks:
                    print(f"[DEBUG Save]   - thinking block has signature: {bool(tb.get('signature'))}", flush=True)
                # Save filtered content blocks (thinking + text only) to DB
                repo.add_message(self.session_id, "assistant", saveable_content)
            yield {"type": "complete", "message": final_text}

    async def _stream_with_sdk(
        self,
        messages: list[dict],
        repo: SessionRepository,
        accumulated_text: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream response using Anthropic SDK (for API key auth)"""
        async with self.client.messages.stream(
            model=settings.model,
            max_tokens=settings.max_tokens,
            system=self.system_prompt,
            messages=messages,
            tools=self._get_tools_schema(),
        ) as stream:
            current_text = ""

            async for event in stream:
                if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                    current_text += event.delta.text
                    yield {"type": "text_delta", "delta": event.delta.text}

            final_message = await stream.get_final_message()

            # Process tool uses if any
            if final_message.stop_reason == "tool_use":
                tool_results = []
                async for event, results in self._process_tool_uses(final_message.content):
                    yield event
                    tool_results = results

                if tool_results:
                    continued_messages = messages + [
                        {"role": "assistant", "content": final_message.content},
                        {"role": "user", "content": tool_results},
                    ]

                    # Continue with accumulated text
                    new_accumulated = accumulated_text + current_text
                    async for event in self._stream_with_sdk(
                        continued_messages, repo, new_accumulated
                    ):
                        yield event
            else:
                final_text = accumulated_text + current_text
                if final_text:
                    repo.add_message(self.session_id, "assistant", final_text)
                yield {"type": "complete", "message": final_text}

    async def _process_tool_uses(
        self,
        content_blocks: list,
    ) -> AsyncGenerator[tuple[dict[str, Any], list[dict]], None]:
        """
        Process tool use blocks and collect results.

        Yields events for each tool and finally yields the tool results list.
        This abstracts the common tool processing logic used by both OAuth and SDK modes.

        Args:
            content_blocks: Content blocks from the response that may contain tool uses

        Yields:
            Tuples of (event, tool_results) where tool_results is populated after each tool
        """
        tool_results = []

        for block in content_blocks:
            block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)

            if block_type == "tool_use":
                tool_id = block.get("id") if isinstance(block, dict) else block.id
                tool_name = block.get("name") if isinstance(block, dict) else block.name
                tool_input = block.get("input", {}) if isinstance(block, dict) else block.input

                async for event in self._handle_tool_use(tool_id, tool_name, tool_input):
                    yield event, tool_results

                    if event["type"] == "tool_end":
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": str(event.get("output", event.get("error", ""))),
                        })

    async def _handle_tool_use(
        self,
        tool_id: str,
        tool_name: str,
        tool_input: dict,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Handle a single tool use, including special handling for AskUserQuestion"""

        # Check plan mode restrictions
        if self.plan_mode and tool_name in PLAN_MODE_BLOCKED_TOOLS:
            yield {
                "type": "tool_start",
                "id": tool_id,
                "name": tool_name,
                "input": tool_input,
            }
            yield {
                "type": "tool_end",
                "id": tool_id,
                "output": f"Tool '{tool_name}' is blocked in Plan Mode. Switch to Implementation Mode to execute write operations.",
                "success": False,
            }
            return

        # Special handling for AskUserQuestion
        if tool_name == "AskUserQuestion":
            yield {
                "type": "tool_start",
                "id": tool_id,
                "name": tool_name,
                "input": tool_input,
            }

            # Send question_prompt to UI
            yield {
                "type": "question_prompt",
                "id": tool_id,
                "questions": tool_input.get("questions", []),
            }

            # Create future and wait for user response
            future: asyncio.Future = asyncio.get_event_loop().create_future()
            self._pending_responses[tool_id] = future

            try:
                # Wait for user response (with timeout)
                user_answers = await asyncio.wait_for(future, timeout=300)  # 5 min timeout

                yield {
                    "type": "tool_end",
                    "id": tool_id,
                    "output": json.dumps({"answers": user_answers}),
                    "success": True,
                }

            except asyncio.TimeoutError:
                yield {
                    "type": "tool_end",
                    "id": tool_id,
                    "output": "User did not respond within timeout",
                    "success": False,
                }

            finally:
                # Clean up
                self._pending_responses.pop(tool_id, None)

            return

        # Normal tool execution
        yield {
            "type": "tool_start",
            "id": tool_id,
            "name": tool_name,
            "input": tool_input,
        }

        result = await self._execute_tool(tool_name, tool_input)

        yield {
            "type": "tool_end",
            "id": tool_id,
            "output": result.get("result") if result.get("success") else result.get("error"),
            "success": result.get("success", True),
        }

    async def _continue_with_tools(
        self,
        messages: list[dict],
        repo: SessionRepository,
        preceding_text: str = "",
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Continue conversation after tool use.

        Args:
            messages: The conversation messages including tool results
            repo: Session repository for persistence
            preceding_text: Text that was streamed before this continuation.
        """
        try:
            await self._ensure_valid_token()

            async with self.client.messages.stream(
                model=settings.model,
                max_tokens=settings.max_tokens,
                system=self.system_prompt,
                messages=messages,
                tools=self._get_tools_schema(),
            ) as stream:
                current_text = ""
                is_first_text_delta = True
                accumulated_text = preceding_text

                async for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, "text"):
                        # Add block separator on first delta if needed
                        if is_first_text_delta and preceding_text:
                            is_first_text_delta = False
                            if not preceding_text.endswith("\n") and not event.delta.text.startswith("\n"):
                                yield {"type": "text_delta", "delta": "\n\n"}
                                current_text += "\n\n"
                                accumulated_text += "\n\n"

                        is_first_text_delta = False
                        current_text += event.delta.text
                        accumulated_text += event.delta.text
                        yield {"type": "text_delta", "delta": event.delta.text}

                final_message = await stream.get_final_message()

                # Handle more tool uses (recursive)
                if final_message.stop_reason == "tool_use":
                    tool_results = []
                    async for event, results in self._process_tool_uses(final_message.content):
                        yield event
                        tool_results = results

                    if tool_results:
                        continued_messages = messages + [
                            {"role": "assistant", "content": final_message.content},
                            {"role": "user", "content": tool_results},
                        ]
                        async for event in self._continue_with_tools(continued_messages, repo, accumulated_text):
                            yield event
                else:
                    if current_text:
                        repo.add_message(self.session_id, "assistant", accumulated_text)
                    yield {"type": "complete", "message": accumulated_text}

        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
            }

    async def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool and return the result"""
        tool = self.tool_registry.get(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
            }

        try:
            result = await tool.execute(tool_input, str(self.workspace_path))
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
