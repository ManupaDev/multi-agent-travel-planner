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
from typing import AsyncIterator, Dict, Any, Optional, Callable
from datetime import datetime

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage, AIMessage

from app.utils.message_extractors import default_message_extractor


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

    async def stream(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
        config: Dict[str, Any],
    ) -> AsyncIterator[str]:
        """
        Stream LangGraph execution as Vercel Data Stream Protocol events.

        This is the main entry point for the adapter. It transforms LangGraph's
        event stream into Vercel-compatible SSE events.

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
        self.current_message_id = self._create_message_id()

        # Send message start event
        yield self._format_sse_event({
            "type": "start",
            "messageId": self.current_message_id,
        })

        # Stream the graph execution
        try:
            async for event in graph.astream_events(
                initial_state,
                config,
                version="v2",
            ):
                # Handle different event types
                async for sse_event in self._handle_event(event):
                    yield sse_event

            # Send finish event after successful completion
            yield self._format_sse_event({
                "type": "finish",
            })

        except Exception as e:
            # Send error event
            yield self._format_sse_event({
                "type": "error",
                "error": str(e),
            })
            return

    async def _handle_event(self, event: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Convert a single LangGraph event to Vercel SSE event(s).

        Args:
            event: LangGraph event dictionary

        Yields:
            SSE-formatted event strings
        """
        event_type = event.get("event")
        event_data = event.get("data", {})

        # Handle tool calls
        if event_type == "on_tool_start":
            async for sse_event in self._handle_tool_start(event):
                yield sse_event

        elif event_type == "on_tool_end":
            async for sse_event in self._handle_tool_end(event):
                yield sse_event

        # Handle state updates (for streaming messages)
        elif event_type == "on_chain_stream":
            async for sse_event in self._handle_chain_stream(event):
                yield sse_event

        # Handle interrupts
        elif event_type == "on_chain_end":
            # Check for interrupts in the final state
            output = event_data.get("output", {})
            if "__interrupt__" in output:
                async for sse_event in self._handle_interrupt(output):
                    yield sse_event

    async def _handle_tool_start(self, event: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Handle tool call start event.

        Yields:
            Tool call SSE events
        """
        tool_name = event.get("name", "unknown_tool")
        tool_input = event.get("data", {}).get("input", {})

        # Generate a unique tool call ID
        tool_call_id = f"call_{uuid.uuid4().hex[:8]}"

        # Send tool call event
        yield self._format_sse_event({
            "type": "tool-call",
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "args": tool_input,
        })

    async def _handle_tool_end(self, event: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Handle tool call completion event.

        Yields:
            Tool result SSE events
        """
        tool_name = event.get("name", "unknown_tool")
        tool_output = event.get("data", {}).get("output")

        # Send tool result event
        yield self._format_sse_event({
            "type": "tool-result",
            "toolName": tool_name,
            "result": tool_output,
        })

    async def _handle_chain_stream(self, event: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Handle state streaming event - extract and stream message content.

        This is where we extract conversational text from the state using
        the configured message_extractor.

        Yields:
            Text delta SSE events
        """
        chunk = event.get("data", {}).get("chunk", {})

        # Try to extract message from the state chunk
        if "messages" in chunk and chunk["messages"]:
            last_message = chunk["messages"][-1]

            # Extract text content
            if isinstance(last_message, BaseMessage):
                text = last_message.content
            elif isinstance(last_message, dict):
                text = last_message.get("content", "")
            else:
                text = str(last_message)

            # Stream the text if we have any
            if text and text.strip():
                # Send text delta event
                yield self._format_sse_event({
                    "type": "text-delta",
                    "id": self.current_message_id,
                    "delta": text,
                })

    async def _handle_interrupt(self, output: Dict[str, Any]) -> AsyncIterator[str]:
        """
        Handle graph interruption (human-in-the-loop).

        Args:
            output: The output dictionary containing interrupt information

        Yields:
            Finish event with interrupt reason and message
        """
        interrupt_value = output.get("__interrupt__", [])

        # Extract interrupt message
        interrupt_message = ""
        if isinstance(interrupt_value, (list, tuple)) and len(interrupt_value) > 0:
            interrupt_obj = interrupt_value[0]
            if hasattr(interrupt_obj, "value"):
                interrupt_message = str(interrupt_obj.value)
            else:
                interrupt_message = str(interrupt_obj)
        else:
            interrupt_message = str(interrupt_value)

        # Send finish event with interrupt
        yield self._format_sse_event({
            "type": "finish",
            "finishReason": "interrupt",
            "interruptMessage": interrupt_message,
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
