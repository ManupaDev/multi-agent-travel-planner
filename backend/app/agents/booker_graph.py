from typing import Optional

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from app.core.llm import model
from app.agents.tools.booking_tools import book_flight, book_hotel, search_hotels
from app.agents.response_models.booker_agent import BookerAgentResponseModel
from app.agents.prompts.travel_system import BOOKER_AGENT_SYSTEM_PROMPT


checkpointer = InMemorySaver()

# Create ToolNode for automatic tool execution
tools = [book_flight, book_hotel, search_hotels]
tool_node = ToolNode(tools)


class BookerGraphState(MessagesState):
    """State for the booker graph."""

    bookings: Optional[dict]
    bookings_complete: bool


def booker_agent_node(state: BookerGraphState) -> BookerGraphState:
    """
    Booker agent node that uses model.bind_tools() for transparent tool calling.

    This allows the streaming adapter to see AIMessage.tool_calls and ToolMessages,
    enabling real-time tool event streaming (hotel search, flight booking, hotel booking visibility).
    """
    # Bind tools and structured output to model
    model_with_tools = model.bind_tools(tools)
    model_with_structured_output = model_with_tools.with_structured_output(
        BookerAgentResponseModel
    )

    # Prepare messages with system prompt
    messages = [SystemMessage(content=BOOKER_AGENT_SYSTEM_PROMPT)] + state["messages"]

    # Invoke model
    response = model_with_tools.invoke(messages)

    # Check if model wants to call tools (search hotels, book flight, book hotel)
    if hasattr(response, "tool_calls") and response.tool_calls:
        # Return AIMessage with tool_calls - ToolNode will handle execution
        print(f"[BOOKER] Model requesting {len(response.tool_calls)} tool call(s)")
        return {"messages": [response]}

    # No tool calls - get structured bookings response
    structured_response = model_with_structured_output.invoke(messages)
    bookings_response = structured_response.bookings

    # Return complete bookings
    return {
        "messages": [],
        "bookings": bookings_response.model_dump(),
        "bookings_complete": True,
    }


def route_after_booker(state: BookerGraphState) -> str:
    """
    Route after booker_agent executes.

    Routes to:
    - "tools" if the model wants to call tools (search_hotels, book_flight, book_hotel)
    - END if bookings are complete
    """
    # Check if last message has tool calls
    messages = state["messages"]
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

    # No tool calls - bookings should be complete
    return END


# Build graph with tool execution support
graph = StateGraph(BookerGraphState)
graph.add_node("booker_agent", booker_agent_node)
graph.add_node("tools", tool_node)  # ToolNode handles tool execution automatically

# Routing
graph.add_edge(START, "booker_agent")

# After agent, check if tools should be called or if we're done
graph.add_conditional_edges(
    "booker_agent",
    route_after_booker,
    {
        "tools": "tools",  # Execute booking tools
        END: END,  # Bookings complete
    },
)

# After tools execute, loop back to agent
graph.add_edge("tools", "booker_agent")

compiled_graph = graph.compile(checkpointer=checkpointer)
