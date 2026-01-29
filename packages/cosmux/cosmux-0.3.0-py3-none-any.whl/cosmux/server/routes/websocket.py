"""WebSocket endpoint for real-time chat communication"""

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from cosmux.auth.credentials import get_credentials
from cosmux.db.engine import get_session, SessionDep
from cosmux.db.repository import SessionRepository
from cosmux.agent.core import AgentOrchestrator


router = APIRouter()


@router.websocket("/{session_id}/ws")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for bidirectional chat communication.

    Message Protocol:

    Client -> Server:
        {"type": "message", "content": "user message text"}
        {"type": "question_response", "id": "tool_id", "answers": {"0": "selected option"}}
        {"type": "set_mode", "mode": "plan" | "implementation"}
        {"type": "ping"}

    Server -> Client:
        {"type": "connected", "sessionId": "...", "mode": "implementation"}
        {"type": "text_delta", "delta": "..."}
        {"type": "tool_start", "id": "...", "name": "...", "input": {...}}
        {"type": "tool_end", "id": "...", "output": "...", "success": true/false}
        {"type": "question_prompt", "id": "...", "questions": [...]}
        {"type": "mode_changed", "mode": "plan" | "implementation"}
        {"type": "thinking", "text": "..."}
        {"type": "complete", "message": "..."}
        {"type": "error", "message": "..."}
        {"type": "pong"}
    """
    await websocket.accept()

    # Check for valid credentials first
    creds = get_credentials()
    if not creds:
        await websocket.send_json({
            "type": "error",
            "message": "Not authenticated. Please login first.",
            "code": "AUTH_REQUIRED",
        })
        await websocket.close(code=4001)
        return

    # Get database session manually (WebSocket doesn't support Depends the same way)
    db = next(get_session())

    # Track the current streaming task and send task
    streaming_task: asyncio.Task | None = None
    send_task: asyncio.Task | None = None
    is_connected = True

    try:
        repo = SessionRepository(db)
        session = repo.get_session(session_id)

        if not session:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close(code=4004)
            return

        # Create agent orchestrator
        agent = AgentOrchestrator(
            workspace_path=session.workspace_path,
            session_id=session_id,
            db=db,
        )

        # Send connection acknowledgement with current mode
        await websocket.send_json({
            "type": "connected",
            "sessionId": session_id,
            "mode": "plan" if agent.plan_mode else "implementation",
        })

        # Queue for events from streaming task to send to client
        event_queue: asyncio.Queue = asyncio.Queue()

        async def stream_to_queue(content: str):
            """Run agent streaming and put events in queue"""
            try:
                async for event in agent.stream_response(content, repo):
                    await event_queue.put(event)
            except Exception as e:
                error_str = str(e)
                error_msg = f"Agent error: {error_str}"
                error_code = None

                # Detect specific API errors and provide actionable messages
                if "tool_use_id" in error_str and "tool_result" in error_str:
                    error_msg = (
                        "Session data is corrupted (tool_use/tool_result mismatch). "
                        "Please clear your session and try again."
                    )
                    error_code = "SESSION_CORRUPTED"
                elif "thinking" in error_str and "cannot be modified" in error_str:
                    error_msg = (
                        "Session data is corrupted (thinking block modified). "
                        "Please clear your session and try again."
                    )
                    error_code = "SESSION_CORRUPTED"
                elif "Anthropic API error" in error_str:
                    # Extract just the relevant part of API errors
                    error_code = "API_ERROR"

                event = {
                    "type": "error",
                    "message": error_msg,
                }
                if error_code:
                    event["code"] = error_code

                await event_queue.put(event)
            finally:
                # Signal streaming is done
                await event_queue.put(None)

        async def send_events():
            """Send events from queue to websocket"""
            nonlocal is_connected
            while is_connected:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    if event is None:
                        break
                    if is_connected:
                        await websocket.send_json(event)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        # Main message loop
        while True:
            try:
                # If we have an active streaming task, we need to handle both
                # receiving messages AND sending events concurrently
                if streaming_task and not streaming_task.done():
                    # Create a task for receiving the next message
                    receive_task = asyncio.create_task(websocket.receive_json())

                    # Wait for either a message or streaming to complete
                    done, pending = await asyncio.wait(
                        [receive_task, streaming_task],
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    # If receive completed, process the message
                    if receive_task in done:
                        data = receive_task.result()
                    else:
                        # Streaming completed, cancel receive and wait for next message
                        receive_task.cancel()
                        try:
                            await receive_task
                        except asyncio.CancelledError:
                            pass
                        streaming_task = None
                        continue
                else:
                    # No active streaming, just wait for messages
                    data = await websocket.receive_json()

                msg_type = data.get("type")

                if msg_type == "message":
                    content = data.get("content", "")
                    if not content.strip():
                        await websocket.send_json({
                            "type": "error",
                            "message": "Empty message",
                        })
                        continue

                    # Note: User message is saved by stream_response after getting history
                    # to avoid duplicate messages in Claude's context

                    # Start streaming in background task
                    streaming_task = asyncio.create_task(stream_to_queue(content))

                    # Also start sending events (track the task)
                    send_task = asyncio.create_task(send_events())

                elif msg_type == "question_response":
                    # User responded to AskUserQuestion
                    tool_id = data.get("id")
                    answers = data.get("answers", {})

                    if not tool_id:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Missing tool id in question_response",
                        })
                        continue

                    # Forward response to agent (this unblocks the waiting future)
                    await agent.receive_user_response(tool_id, answers)

                elif msg_type == "set_mode":
                    # Switch between plan and implementation mode
                    mode = data.get("mode", "implementation")

                    if mode not in ("plan", "implementation"):
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Invalid mode: {mode}. Use 'plan' or 'implementation'",
                        })
                        continue

                    agent.set_plan_mode(mode == "plan")

                    await websocket.send_json({
                        "type": "mode_changed",
                        "mode": mode,
                    })

                elif msg_type == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({"type": "pong"})

                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown message type: {msg_type}",
                    })

            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON",
                })

    except WebSocketDisconnect:
        # Client disconnected gracefully
        pass
    except Exception as e:
        # Unexpected error
        try:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}",
            })
        except:
            pass
    finally:
        # Mark as disconnected to stop send_events loop
        is_connected = False

        # Cancel any running tasks
        if streaming_task and not streaming_task.done():
            streaming_task.cancel()
            try:
                await streaming_task
            except asyncio.CancelledError:
                pass

        if send_task and not send_task.done():
            send_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass

        # Clean up database session
        db.close()
