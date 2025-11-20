"""
Streaming service for the travel system chat endpoint.

This module provides async streaming functionality for the full travel
system pipeline using the Vercel Data Stream Protocol.
"""

from typing import AsyncGenerator, Any, Dict
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.travel_system_graph import travel_system_graph
from app.utils.vercel_stream import stream_langgraph_to_vercel


async def stream_travel_system_chat(
    message: str,
    thread_id: str,
    resume: bool = False
) -> AsyncGenerator[str, None]:
    """
    Stream the travel system chat execution as Vercel protocol events.

    This function orchestrates the full pipeline:
    1. Requirements gathering (with potential interrupts)
    2. Itinerary planning
    3. Booking execution

    Args:
        message: User message or resume input
        thread_id: Thread ID for conversation continuity
        resume: Whether to resume from an interrupt

    Yields:
        SSE-formatted strings following Vercel Data Stream Protocol
    """
    config = {"configurable": {"thread_id": thread_id}}

    if resume:
        # Resume execution with user input
        initial_state = Command(resume=message)
    else:
        # Initial invocation
        from app.agents.travel_system_graph import TravelSystemState

        initial_state = TravelSystemState(
            messages=[HumanMessage(content=message)],
            requirements=None,
            itinerary=None,
            bookings=None,
        )

    # Stream the graph execution
    async for event in stream_langgraph_to_vercel(
        graph=travel_system_graph,
        initial_state=initial_state,
        config=config,
        stream_mode="values"  # Use values to get full state updates
    ):
        yield event
