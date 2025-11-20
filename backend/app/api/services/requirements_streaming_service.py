"""
Streaming service for the requirements gathering chat endpoint.

This module provides async streaming functionality for requirements
gathering using the Vercel Data Stream Protocol.
"""

from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.requirements_graph import compiled_graph, RequirementsGraphState
from app.utils.vercel_stream import stream_langgraph_to_vercel


async def stream_requirements_chat(
    message: str,
    thread_id: str,
    resume: bool = False
) -> AsyncGenerator[str, None]:
    """
    Stream the requirements gathering execution as Vercel protocol events.

    This function handles interactive requirements gathering with
    potential interrupts when information is missing.

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
        initial_state = RequirementsGraphState(
            messages=[HumanMessage(content=message)],
            requirements_complete=False,
            interruption_message="",
            requirements=None,
        )

    # Stream the graph execution
    async for event in stream_langgraph_to_vercel(
        graph=compiled_graph,
        initial_state=initial_state,
        config=config,
        stream_mode="values"  # Use values to get full state updates
    ):
        yield event
