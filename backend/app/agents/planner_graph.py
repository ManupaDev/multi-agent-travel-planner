from typing import Optional

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from app.core.llm import model
from app.agents.tools.planner_tools import web_search
from app.agents.response_models.planner_agent import PlannerAgentResponseModel
from app.agents.prompts.travel_system import PLANNER_AGENT_SYSTEM_PROMPT


checkpointer = InMemorySaver()

# Create ToolNode for automatic tool execution
tools = [web_search]
tool_node = ToolNode(tools)


class PlannerGraphState(MessagesState):
    """State for the planner graph."""

    itinerary: Optional[dict]
    itinerary_complete: bool


def planner_agent_node(state: PlannerGraphState) -> PlannerGraphState:
    """
    Planner agent node that uses model.bind_tools() for transparent tool calling.

    This allows the streaming adapter to see AIMessage.tool_calls and ToolMessages,
    enabling real-time tool event streaming (web search visibility).
    """
    # Bind tools and structured output to model
    model_with_tools = model.bind_tools(tools)
    model_with_structured_output = model_with_tools.with_structured_output(
        PlannerAgentResponseModel
    )

    # Prepare messages with system prompt
    messages = [SystemMessage(content=PLANNER_AGENT_SYSTEM_PROMPT)] + state["messages"]

    # Invoke model
    response = model_with_tools.invoke(messages)

    # Check if model wants to call tools (web search for attractions/POIs)
    if hasattr(response, "tool_calls") and response.tool_calls:
        # Return AIMessage with tool_calls - ToolNode will handle execution
        print(f"[PLANNER] Model requesting {len(response.tool_calls)} tool call(s)")
        return {"messages": [response]}

    # No tool calls - get structured itinerary response
    structured_response = model_with_structured_output.invoke(messages)
    itinerary_response = structured_response.itinerary

    # Return complete itinerary
    return {
        "messages": [],
        "itinerary": itinerary_response.model_dump(),
        "itinerary_complete": True,
    }


def route_after_planner(state: PlannerGraphState) -> str:
    """
    Route after planner_agent executes.

    Routes to:
    - "tools" if the model wants to call tools (web search)
    - END if itinerary is complete
    """
    # Check if last message has tool calls
    messages = state["messages"]
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

    # No tool calls - itinerary should be complete
    return END


# Build graph with tool execution support
graph = StateGraph(PlannerGraphState)
graph.add_node("planner_agent", planner_agent_node)
graph.add_node("tools", tool_node)  # ToolNode handles tool execution automatically

# Routing
graph.add_edge(START, "planner_agent")

# After agent, check if tools should be called or if we're done
graph.add_conditional_edges(
    "planner_agent",
    route_after_planner,
    {
        "tools": "tools",  # Execute web search
        END: END,  # Itinerary complete
    },
)

# After tools execute, loop back to agent
graph.add_edge("tools", "planner_agent")

compiled_graph = graph.compile(checkpointer=checkpointer)
