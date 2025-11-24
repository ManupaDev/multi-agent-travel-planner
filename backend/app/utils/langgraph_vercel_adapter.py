"""
Pluggable adapter for converting LangGraph event streams to Vercel Data Stream Protocol.

This module provides a clean separation between LangGraph's agentic logic and
Vercel's streaming protocol, allowing any LangGraph graph to work with Vercel AI SDK
frontend hooks (useChat, useAssistant) without modifying core agent logic.

Standard Contract for LangGraph Graphs:
    1. State must extend MessagesState (contains 'messages' field)
    2. Nodes should return AIMessage objects for conversational responses
    3. No other requirements - the adapter handles the rest!

Usage:
    adapter = LangGraphToVercelAdapter()

    async for sse_event in adapter.stream(
        graph=your_graph,
        initial_state=initial_state,
        config=config
    ):
        yield sse_event
"""

import json
import uuid
import logging
from typing import AsyncIterator, Dict, Any, Optional, Callable
from datetime import datetime

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

from app.utils.message_extractors import default_message_extractor

logger = logging.getLogger(__name__)


class LangGraphToVercelAdapter:
    """
    Converts LangGraph event streams to Vercel Data Stream Protocol (SSE format).

    This adapter provides a pluggable streaming layer that works with any
    LangGraph graph following the minimal standard contract.
    """

    def __init__(
        self,
        message_extractor: Optional[Callable[[Dict[str, Any]], str]] = None,
        include_reasoning: bool = False,
    ):
        """
        Initialize the adapter.

        Args:
            message_extractor: Custom function to extract text from state.
                             Defaults to extracting from messages[-1].content
            include_reasoning: Whether to include reasoning in the stream
                             (for models that support chain-of-thought)
        """
        self.message_extractor = message_extractor or default_message_extractor
        self.include_reasoning = include_reasoning
        self.current_message_id: Optional[str] = None

    def _format_sse_event(self, data: Dict[str, Any]) -> str:
        """
        Format a dictionary as a Server-Sent Event.

        Args:
            data: Dictionary to send as SSE event

        Returns:
            Formatted SSE string

        Example:
            >>> adapter._format_sse_event({"type": "text-delta", "delta": "Hello"})
            'data: {"type":"text-delta","delta":"Hello"}\\n\\n'
        """
        return f"data: {json.dumps(data)}\n\n"

    def _create_message_id(self) -> str:
        """Generate a unique message ID for Vercel protocol."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"msg_{timestamp}_{unique_id}"

    async def _handle_tool_calls(self, message: AIMessage) -> AsyncIterator[str]:
        """
        Stream tool events from AIMessage.tool_calls following Vercel Data Stream Protocol.

        Sends tool-input-start followed by tool-input-available events.

        Args:
            message: AIMessage that may contain tool_calls

        Yields:
            SSE-formatted tool events (tool-input-start, tool-input-available)
        """
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return

        print(f"[TOOL] Found {len(message.tool_calls)} tool call(s)")
        logger.info(f"[TOOL] Processing {len(message.tool_calls)} tool calls")

        for tool_call in message.tool_calls:
            tool_call_id = tool_call.get("id") or str(uuid.uuid4())
            tool_name = tool_call.get("name", "unknown_tool")
            tool_args = tool_call.get("args", {})

            print(f"[TOOL] Tool call: {tool_name} with ID: {tool_call_id}")
            logger.info(f"[TOOL] Streaming tool-input-start: {tool_name}(args={tool_args})")

            # Send tool-input-start event (signals tool call beginning)
            yield self._format_sse_event({
                "type": "tool-input-start",
                "toolCallId": tool_call_id,
                "toolName": tool_name,
            })

            # Send tool-input-available event (complete parameters)
            yield self._format_sse_event({
                "type": "tool-input-available",
                "toolCallId": tool_call_id,
                "toolName": tool_name,
                "input": tool_args,
            })

    async def _handle_tool_result(self, message: ToolMessage) -> AsyncIterator[str]:
        """
        Stream tool output events from ToolMessage following Vercel Data Stream Protocol.

        Args:
            message: ToolMessage containing tool execution result

        Yields:
            SSE-formatted tool-output-available events
        """
        tool_call_id = message.tool_call_id if hasattr(message, "tool_call_id") else "unknown"
        result_content = message.content

        print(f"[TOOL] Tool result for call ID: {tool_call_id}")
        logger.info(f"[TOOL] Streaming tool-output-available for {tool_call_id}: {result_content[:100] if result_content else 'empty'}")

        # Send tool-output-available event (tool execution result)
        yield self._format_sse_event({
            "type": "tool-output-available",
            "toolCallId": tool_call_id,
            "output": result_content,
        })

    async def stream(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
        config: Dict[str, Any],
    ) -> AsyncIterator[str]:
        """
        Stream LangGraph execution as Vercel Data Stream Protocol events.

        This is the main entry point for the adapter. It transforms LangGraph's
        state updates into Vercel-compatible SSE events.

        Args:
            graph: The compiled LangGraph graph to execute
            initial_state: Initial state dictionary for the graph
            config: Configuration dict (must include thread_id in configurable)

        Yields:
            SSE-formatted strings ready to send to the frontend

        Example:
            async for event in adapter.stream(my_graph, initial_state, config):
                # event is like: 'data: {"type":"text-delta","delta":"Hello"}\\n\\n'
                response.write(event)
        """
        # Stream the graph execution
        logger.info(f"[ADAPTER] Starting stream with config: {config}")
        logger.info(f"[ADAPTER] Initial state type: {type(initial_state)}")

        try:
            chunk_count = 0
            async for chunk in graph.astream(
                initial_state,
                config,
                stream_mode="updates",  # Changed from "values" to "updates"
                subgraphs=True,  # Enable subgraph event streaming (native LangGraph feature)
            ):
                chunk_count += 1
                print(f"\n[ADAPTER] ===== Received chunk #{chunk_count} =====")
                print(f"[ADAPTER] Chunk type: {type(chunk)}")

                # With subgraphs=True, chunks are tuples: (namespace, state_update)
                # namespace is () for parent graph, ('node_name:uuid',) for subgraphs
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    namespace, state_update = chunk
                    print(f"[ADAPTER] Namespace: {namespace}")
                    print(f"[ADAPTER] State update keys: {list(state_update.keys())}")
                    logger.info(f"[ADAPTER] Received chunk #{chunk_count}: namespace={namespace}, keys={list(state_update.keys())}")

                    # Process the state update
                    async for sse_event in self._handle_node_update(state_update):
                        logger.info(f"[ADAPTER] Yielding SSE event: {sse_event[:100]}...")
                        yield sse_event
                else:
                    # Fallback for non-tuple chunks (shouldn't happen with subgraphs=True)
                    print(f"[ADAPTER] Non-tuple chunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'N/A'}")
                    logger.info(f"[ADAPTER] Received non-tuple chunk #{chunk_count}: {list(chunk.keys()) if isinstance(chunk, dict) else type(chunk)}")
                    async for sse_event in self._handle_node_update(chunk):
                        logger.info(f"[ADAPTER] Yielding SSE event: {sse_event[:100]}...")
                        yield sse_event

            logger.info(f"[ADAPTER] Stream completed. Total chunks: {chunk_count}")

            # Send finish event after successful completion
            yield self._format_sse_event({
                "type": "finish",
            })

            # Terminate stream with [DONE]
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[ADAPTER] Error during streaming: {e}", exc_info=True)
            # Send error event
            yield self._format_sse_event({
                "type": "error",
                "error": str(e),
            })
            return

    async def _handle_node_update(self, chunk: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Process state updates from astream(stream_mode="updates", subgraphs=True).

        Args:
            chunk: The state update dict from a single node execution
                  Format: {'messages': [...], 'requirements': ..., 'itinerary': ..., 'bookings': ...}
                  With subgraphs=True, this receives updates from both parent and subgraph nodes

        Yields:
            SSE-formatted event strings
        """
        # With stream_mode="updates", chunk contains the state updates from a node
        state = chunk
        print(f"[STATE] Processing state with keys: {list(state.keys())}")
        logger.info(f"[STATE] Processing state with keys: {list(state.keys())}")

        # Check for interrupt first
        if "__interrupt__" in state:
            print(f"[STATE] Interrupt detected")
            logger.info(f"[STATE] Interrupt detected")
            async for sse_event in self._handle_interrupt(state):
                yield sse_event
            return  # Stop processing after interrupt

        # Extract and stream messages
        if "messages" in state:
            messages = state["messages"]
            print(f"[STATE] Found {len(messages) if messages else 0} messages")
            logger.info(f"[STATE] Found {len(messages) if messages else 0} messages")

            if messages:
                # Get the last message (most recent addition)
                last_message = messages[-1]
                print(f"[STATE] Last message type: {type(last_message)}")
                logger.info(f"[STATE] Last message type: {type(last_message)}")

                # Handle ToolMessage (tool execution results)
                if isinstance(last_message, ToolMessage):
                    print(f"[STATE] Processing ToolMessage")
                    logger.info(f"[STATE] Processing ToolMessage")
                    async for sse_event in self._handle_tool_result(last_message):
                        yield sse_event
                    return

                # Only stream AIMessage content (not HumanMessage)
                # User messages are already in the frontend
                if not isinstance(last_message, AIMessage):
                    print(f"[STATE] Skipping non-AI message")
                    logger.info(f"[STATE] Skipping non-AI message")
                    return  # Don't stream user messages

                # Check for tool calls first (before streaming text)
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    print(f"[STATE] AIMessage has {len(last_message.tool_calls)} tool calls")
                    logger.info(f"[STATE] AIMessage has {len(last_message.tool_calls)} tool calls")
                    async for sse_event in self._handle_tool_calls(last_message):
                        yield sse_event

                # Extract content from AI message
                content = None
                if isinstance(last_message, BaseMessage):
                    content = last_message.content
                elif isinstance(last_message, dict):
                    content = last_message.get("content", "")
                else:
                    content = str(last_message)

                print(f"[STATE] Extracted content length: {len(content) if content else 0}")
                logger.info(f"[STATE] Extracted content length: {len(content) if content else 0}")
                if content:
                    print(f"[STATE] Content preview: {content[:100]}")
                    logger.info(f"[STATE] Content preview: {content[:100]}")

                # Stream the content if available
                if content and content.strip():
                    # Create unique message ID for this message
                    message_id = self._create_message_id()
                    print(f"[STATE] Streaming message with ID: {message_id}")
                    logger.info(f"[STATE] Streaming message with ID: {message_id}")

                    # Send text-start event
                    yield self._format_sse_event({
                        "type": "text-start",
                        "id": message_id,
                    })

                    # Send text-delta event
                    yield self._format_sse_event({
                        "type": "text-delta",
                        "id": message_id,
                        "delta": content,
                    })

                    # Send text-end event
                    yield self._format_sse_event({
                        "type": "text-end",
                        "id": message_id,
                    })
                else:
                    logger.warning(f"[STATE] Content is empty or whitespace only")
            else:
                logger.warning(f"[STATE] Messages array is empty")
        else:
            logger.warning(f"[STATE] No 'messages' key in state")

        # Optionally stream custom data fields (for travel planner use case)
        if "requirements" in state and state["requirements"]:
            yield self._format_sse_event({
                "type": "data-requirements",
                "data": state["requirements"],
            })

        if "itinerary" in state and state["itinerary"]:
            yield self._format_sse_event({
                "type": "data-itinerary",
                "data": state["itinerary"],
            })

        if "bookings" in state and state["bookings"]:
            yield self._format_sse_event({
                "type": "data-bookings",
                "data": state["bookings"],
            })

    async def _handle_interrupt(self, state_update: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Handle graph interruption (human-in-the-loop).

        When a LangGraph node calls interrupt(message), LangGraph stores an Interrupt
        object in state["__interrupt__"] as a list. We extract the message and stream
        it as text-delta events, then send a finish event with interrupt reason.

        Args:
            state_update: The state update containing interrupt information

        Yields:
            Text events with interrupt message, then finish event
        """
        interrupt_list = state_update.get("__interrupt__", [])
        print(f"[INTERRUPT] Interrupt list length: {len(interrupt_list) if isinstance(interrupt_list, list) else 'N/A'}")
        logger.info(f"[INTERRUPT] Interrupt list type: {type(interrupt_list)}, length: {len(interrupt_list) if isinstance(interrupt_list, list) else 'N/A'}")

        # Extract the interrupt message from the Interrupt object
        # Format: [Interrupt(value="message")]
        interrupt_message = ""
        if interrupt_list:
            interrupt_obj = interrupt_list[0]
            logger.info(f"[INTERRUPT] Interrupt object type: {type(interrupt_obj)}")

            # Interrupt objects have a .value attribute
            if hasattr(interrupt_obj, "value"):
                interrupt_message = str(interrupt_obj.value)
                print(f"[INTERRUPT] Extracted message: {interrupt_message[:100]}...")
                logger.info(f"[INTERRUPT] Extracted message from .value: {interrupt_message}")
            else:
                # Fallback if structure is different
                interrupt_message = str(interrupt_obj)
                logger.info(f"[INTERRUPT] Using string representation: {interrupt_message}")

        # Stream the interrupt message as text events (so frontend displays it)
        if interrupt_message:
            message_id = self._create_message_id()
            print(f"[INTERRUPT] Streaming interrupt message with ID: {message_id}")
            logger.info(f"[INTERRUPT] Streaming interrupt message with ID: {message_id}")

            # Send text-start event
            yield self._format_sse_event({
                "type": "text-start",
                "id": message_id,
            })

            # Send text-delta event with interrupt message
            yield self._format_sse_event({
                "type": "text-delta",
                "id": message_id,
                "delta": interrupt_message,
            })

            # Send text-end event
            yield self._format_sse_event({
                "type": "text-end",
                "id": message_id,
            })

        # Send finish event with interrupt reason
        print(f"[INTERRUPT] Sending finish event")
        logger.info(f"[INTERRUPT] Sending finish event with interrupt reason")
        yield self._format_sse_event({
            "type": "finish",
            "finishReason": "interrupt",
        })

    async def stream_with_final_state(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
        config: Dict[str, Any],
    ) -> tuple[AsyncIterator[str], Dict[str, Any]]:
        """
        Stream execution and return final state.

        This is useful when you need both the stream for the frontend
        and the final state for logging/processing.

        Args:
            graph: The compiled LangGraph graph
            initial_state: Initial state dictionary
            config: Configuration dict

        Returns:
            Tuple of (event iterator, final state dict)
        """
        final_state = None

        async def _stream_and_capture():
            nonlocal final_state
            async for event in self.stream(graph, initial_state, config):
                yield event

            # Capture final state after streaming completes
            final_state = await graph.aget_state(config)

        return _stream_and_capture(), final_state


# Convenience function for common use case
async def stream_langgraph_to_vercel(
    graph: StateGraph,
    initial_state: Dict[str, Any],
    config: Dict[str, Any],
    message_extractor: Optional[Callable] = None,
) -> AsyncIterator[str]:
    """
    Convenience function to stream a LangGraph graph to Vercel protocol.

    Args:
        graph: The compiled LangGraph graph to execute
        initial_state: Initial state dictionary for the graph
        config: Configuration dict (must include thread_id)
        message_extractor: Optional custom message extractor

    Yields:
        SSE-formatted event strings

    Example:
        async for event in stream_langgraph_to_vercel(my_graph, state, config):
            yield event
    """
    adapter = LangGraphToVercelAdapter(message_extractor=message_extractor)
    async for event in adapter.stream(graph, initial_state, config):
        yield event
