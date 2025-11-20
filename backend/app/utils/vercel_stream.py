"""
Vercel AI SDK Data Stream Protocol adapter for LangGraph.

This module provides utilities to convert LangGraph streaming events
into the Vercel Data Stream Protocol format for seamless integration
with the Vercel AI SDK on the frontend.

Reference: https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol
"""

import json
import uuid
import traceback
from typing import Any, AsyncGenerator, Dict, Optional
from fastapi.responses import StreamingResponse


def format_sse(payload: dict) -> str:
    """
    Format a payload as a Server-Sent Event.

    Args:
        payload: Dictionary to be sent as SSE data

    Returns:
        Formatted SSE string with data prefix and double newline
    """
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n"


def patch_vercel_headers(response: StreamingResponse) -> StreamingResponse:
    """
    Add required headers for Vercel AI SDK compatibility.

    Args:
        response: FastAPI StreamingResponse to patch

    Returns:
        Response with added headers
    """
    response.headers["x-vercel-ai-ui-message-stream"] = "v1"
    response.headers["x-vercel-ai-protocol"] = "data"
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"

    return response


async def stream_langgraph_to_vercel(
    graph,
    initial_state: Any,
    config: Dict[str, Any],
    stream_mode: str = "messages",
) -> AsyncGenerator[str, None]:
    """
    Stream LangGraph execution as Vercel Data Stream Protocol events.

    This function monitors LangGraph's streaming events and converts them
    to the Vercel protocol format, handling:
    - LLM token streaming (text-delta events)
    - Tool calls (tool-input-* and tool-output-* events)
    - Interrupts (special finish event with metadata)
    - Final structured data (attached to finish event)

    Args:
        graph: Compiled LangGraph instance
        initial_state: Initial state or Command for the graph
        config: Configuration dict (must include thread_id)
        stream_mode: LangGraph stream mode (default: "messages")

    Yields:
        SSE-formatted strings for each event
    """
    try:
        message_id = f"msg-{uuid.uuid4().hex}"
        text_stream_id = "text-1"
        text_started = False

        # Send start event
        yield format_sse({"type": "start", "messageId": message_id})

        # Track the final state for structured data
        final_state = None
        interrupted = False
        interrupt_message = ""

        # Stream graph execution
        async for event in graph.astream(initial_state, config, stream_mode=stream_mode):

            # Check for interrupts in the state
            if isinstance(event, dict) and "__interrupt__" in event:
                interrupted = True
                interrupt_value = event["__interrupt__"]

                # Extract interrupt message
                if isinstance(interrupt_value, (list, tuple)) and len(interrupt_value) > 0:
                    interrupt_obj = interrupt_value[0]
                    if hasattr(interrupt_obj, "value"):
                        interrupt_message = str(interrupt_obj.value)
                    else:
                        interrupt_message = str(interrupt_obj)
                else:
                    interrupt_message = str(interrupt_value)

                # Stream the interrupt message as text
                if not text_started:
                    yield format_sse({"type": "text-start", "id": text_stream_id})
                    text_started = True

                yield format_sse({
                    "type": "text-delta",
                    "id": text_stream_id,
                    "delta": interrupt_message
                })

                # Store state and break
                final_state = event
                break

            # Handle message streaming (for "messages" mode)
            if stream_mode == "messages":
                # Event is a tuple: (message, metadata)
                if isinstance(event, tuple) and len(event) == 2:
                    message, metadata = event

                    # Check if message has content
                    if hasattr(message, "content") and message.content:
                        if not text_started:
                            yield format_sse({"type": "text-start", "id": text_stream_id})
                            text_started = True

                        # Stream the content chunk
                        yield format_sse({
                            "type": "text-delta",
                            "id": text_stream_id,
                            "delta": message.content
                        })

            # Handle values/updates streaming
            elif stream_mode in ["values", "updates"]:
                # Store the latest state
                final_state = event

                # Check if there are messages to stream
                if isinstance(event, dict):
                    messages = event.get("messages", [])

                    # Stream the last message if it's from assistant
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "content") and last_message.content:
                            if hasattr(last_message, "type") and last_message.type == "ai":
                                if not text_started:
                                    yield format_sse({"type": "text-start", "id": text_stream_id})
                                    text_started = True

                                yield format_sse({
                                    "type": "text-delta",
                                    "id": text_stream_id,
                                    "delta": last_message.content
                                })

        # End text stream if it was started
        if text_started:
            yield format_sse({"type": "text-end", "id": text_stream_id})

        # Send structured data as data-{type} events (Vercel protocol compliant)
        if not interrupted and final_state and isinstance(final_state, dict):
            # Send requirements as data-requirements event
            if "requirements" in final_state and final_state["requirements"]:
                yield format_sse({
                    "type": "data-requirements",
                    "data": final_state["requirements"]
                })

            # Send itinerary as data-itinerary event
            if "itinerary" in final_state and final_state["itinerary"]:
                yield format_sse({
                    "type": "data-itinerary",
                    "data": final_state["itinerary"]
                })

            # Send bookings as data-bookings event
            if "bookings" in final_state and final_state["bookings"]:
                yield format_sse({
                    "type": "data-bookings",
                    "data": final_state["bookings"]
                })

        # Prepare finish metadata (only for interrupts)
        finish_metadata: Dict[str, Any] = {}

        if interrupted:
            # Mark as interrupted
            finish_metadata["interrupt"] = True
            finish_metadata["interruptMessage"] = interrupt_message

        # Send finish event
        if finish_metadata:
            yield format_sse({"type": "finish", "messageMetadata": finish_metadata})
        else:
            yield format_sse({"type": "finish"})

        # Send done marker
        yield "data: [DONE]\n\n"

    except Exception as e:
        # Log the error
        traceback.print_exc()

        # Send error event
        yield format_sse({
            "type": "error",
            "error": str(e)
        })

        yield "data: [DONE]\n\n"


async def stream_langgraph_events_to_vercel(
    graph,
    initial_state: Any,
    config: Dict[str, Any],
) -> AsyncGenerator[str, None]:
    """
    Stream LangGraph execution using astream_events for fine-grained control.

    This provides more detailed streaming by monitoring individual events like:
    - on_chat_model_stream: Individual LLM tokens
    - on_tool_start: Tool invocation beginning
    - on_tool_end: Tool execution completion

    Args:
        graph: Compiled LangGraph instance
        initial_state: Initial state or Command for the graph
        config: Configuration dict (must include thread_id)

    Yields:
        SSE-formatted strings for each event
    """
    try:
        message_id = f"msg-{uuid.uuid4().hex}"
        text_stream_id = "text-1"
        text_started = False
        tool_calls: Dict[str, Dict[str, Any]] = {}

        # Send start event
        yield format_sse({"type": "start", "messageId": message_id})

        final_state = None
        interrupted = False
        interrupt_message = ""

        # Stream events
        async for event in graph.astream_events(initial_state, config, version="v2"):
            event_type = event.get("event")
            event_data = event.get("data", {})

            # Handle LLM token streaming
            if event_type == "on_chat_model_stream":
                chunk = event_data.get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    if not text_started:
                        yield format_sse({"type": "text-start", "id": text_stream_id})
                        text_started = True

                    yield format_sse({
                        "type": "text-delta",
                        "id": text_stream_id,
                        "delta": chunk.content
                    })

            # Handle tool calls
            elif event_type == "on_tool_start":
                tool_name = event.get("name")
                tool_id = f"tool-{uuid.uuid4().hex[:8]}"

                tool_calls[tool_id] = {
                    "name": tool_name,
                    "input": event_data.get("input", {})
                }

                yield format_sse({
                    "type": "tool-input-start",
                    "toolCallId": tool_id,
                    "toolName": tool_name
                })

                yield format_sse({
                    "type": "tool-input-available",
                    "toolCallId": tool_id,
                    "toolName": tool_name,
                    "input": event_data.get("input", {})
                })

            elif event_type == "on_tool_end":
                # Find matching tool call
                tool_name = event.get("name")
                tool_output = event_data.get("output")

                # Use last tool call ID for this tool name
                matching_id = None
                for tid, tdata in tool_calls.items():
                    if tdata["name"] == tool_name:
                        matching_id = tid

                if matching_id:
                    yield format_sse({
                        "type": "tool-output-available",
                        "toolCallId": matching_id,
                        "output": tool_output
                    })

        # Check final state for interrupts
        # Note: With astream_events, we need to check the final state differently
        # We'll use astream in parallel to detect interrupts

        # End text stream if started
        if text_started:
            yield format_sse({"type": "text-end", "id": text_stream_id})

        # Send finish event
        yield format_sse({"type": "finish"})
        yield "data: [DONE]\n\n"

    except Exception as e:
        traceback.print_exc()
        yield format_sse({"type": "error", "error": str(e)})
        yield "data: [DONE]\n\n"
