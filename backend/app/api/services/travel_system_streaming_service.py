"""
Pluggable adapter-based streaming service for the travel system.

This demonstrates how to use the LangGraphToVercelAdapter for clean
separation of concerns between agentic logic and streaming protocol.

Key features:
- Uses pluggable adapter instead of tightly-coupled streaming
- No graph-specific logic in streaming layer
- Easily reusable with other LangGraph graphs
- Customizable message extraction strategies
"""

from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.travel_system_graph import travel_system_graph, TravelSystemState
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel


async def stream_travel_system_chat(
    message: str,
    thread_id: str,
    resume: bool = False
) -> AsyncGenerator[str, None]:
    """
    Stream the travel system using the pluggable adapter.

    This uses the LangGraphToVercelAdapter which provides:
    - Clean separation between graph logic and streaming
    - Works with any LangGraph graph
    - No hardcoded field checks (requirements, itinerary, bookings)
    - Pluggable message extraction

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
        initial_state = TravelSystemState(
            messages=[HumanMessage(content=message)],
            requirements=None,
            itinerary=None,
            bookings=None,
        )

    # Stream using the pluggable adapter!
    # No need to specify stream_mode or graph-specific logic
    async for event in stream_langgraph_to_vercel(
        graph=travel_system_graph,
        initial_state=initial_state,
        config=config,
    ):
        yield event


# Example: Custom extractor for specific use case
async def stream_travel_system_with_custom_extractor(
    message: str,
    thread_id: str,
    resume: bool = False
) -> AsyncGenerator[str, None]:
    """
    Demonstrates using a custom message extractor.

    This could be useful if you want to extract messages from a specific
    field or combine multiple fields into the conversational text.
    """
    from app.utils.message_extractors import MessageExtractorChain, summary_field_extractor, default_message_extractor
    from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter

    # Create custom extractor chain
    # Try summary field first, fallback to messages
    extractor = MessageExtractorChain([
        summary_field_extractor,
        default_message_extractor,
    ])

    # Create adapter with custom extractor
    adapter = LangGraphToVercelAdapter(message_extractor=extractor.extract)

    config = {"configurable": {"thread_id": thread_id}}

    if resume:
        initial_state = Command(resume=message)
    else:
        initial_state = TravelSystemState(
            messages=[HumanMessage(content=message)],
            requirements=None,
            itinerary=None,
            bookings=None,
        )

    # Stream using custom adapter
    async for event in adapter.stream(
        graph=travel_system_graph,
        initial_state=initial_state,
        config=config,
    ):
        yield event


# Example: Any other LangGraph graph can use the same adapter!
async def stream_any_langgraph_graph(
    graph,  # Any compiled LangGraph graph
    message: str,
    thread_id: str,
) -> AsyncGenerator[str, None]:
    """
    Generic streaming function that works with ANY LangGraph graph.

    This demonstrates the true power of the pluggable adapter:
    - No graph-specific code
    - No hardcoded field checks
    - Just pass your graph and state

    Requirements:
    - Graph state must extend MessagesState
    - Nodes should return AIMessage objects
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Minimal initial state (works with any MessagesState-based graph)
    initial_state = {
        "messages": [HumanMessage(content=message)]
    }

    # Same adapter works for ANY graph!
    async for event in stream_langgraph_to_vercel(
        graph=graph,
        initial_state=initial_state,
        config=config,
    ):
        yield event
