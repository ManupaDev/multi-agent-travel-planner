import json
from typing import Optional

from langchain.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode

from app.core.llm import model
from app.agents.tools.flight_tools import search_flight_availability
from app.agents.response_models.requirements_agent import RequirementsAgentResponseModel
from app.agents.prompts.travel_system import REQUIREMENTS_AGENT_SYSTEM_PROMPT


checkpointer = InMemorySaver()

# Create ToolNode for automatic tool execution
tools = [search_flight_availability]
tool_node = ToolNode(tools)


class RequirementsGraphState(MessagesState):
    requirements_complete: bool
    interruption_message: str
    requirements: Optional[dict]


def requirements_agent_node(state: RequirementsGraphState) -> RequirementsGraphState:
    """
    Requirements agent node that uses model.bind_tools() for transparent tool calling.

    This allows the streaming adapter to see AIMessage.tool_calls and ToolMessages,
    enabling real-time tool event streaming to the frontend.
    """
    # Bind tools and structured output to model
    model_with_tools = model.bind_tools(tools)
    model_with_structured_output = model_with_tools.with_structured_output(
        RequirementsAgentResponseModel
    )

    # Prepare messages with system prompt
    messages = [SystemMessage(content=REQUIREMENTS_AGENT_SYSTEM_PROMPT)] + state[
        "messages"
    ]

    # Invoke model
    response = model_with_tools.invoke(messages)

    # Check if model wants to call tools
    if hasattr(response, "tool_calls") and response.tool_calls:
        # Return AIMessage with tool_calls - ToolNode will handle execution
        print(f"[REQUIREMENTS] Model requesting {len(response.tool_calls)} tool call(s)")
        return {"messages": [response]}

    # No tool calls - this should be the final response
    # Re-invoke with structured output to get RequirementsAgentResponseModel
    structured_response = model_with_structured_output.invoke(messages)
    requirements_response = structured_response.requirements

    # Check if we need more info from user
    if requirements_response.missing_info.question != "":
        return {
            "messages": [
                AIMessage(content=requirements_response.missing_info.question)
            ],
            "interruption_message": requirements_response.missing_info.question,
            "requirements_complete": False,
            "requirements": None,
        }

    # Requirements are complete
    return {
        "messages": [],
        "requirements_complete": True,
        "interruption_message": "",
        "requirements": requirements_response.model_dump(),
    }


def route_after_agent(state: RequirementsGraphState) -> str:
    """
    Route after requirements_agent executes.

    Routes to:
    - "tools" if the model wants to call tools
    - "ask_user_for_info" if requirements are incomplete (need user input)
    - END if requirements are complete
    """
    # Check if last message has tool calls
    messages = state["messages"]
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

    # No tool calls - check if requirements are complete
    if not state["requirements_complete"]:
        return "ask_user_for_info"

    return END


def ask_user_for_info(state: RequirementsGraphState) -> RequirementsGraphState:
    user_response = interrupt(state["interruption_message"])

    return {
        "messages": [HumanMessage(content=user_response)],
        "interruption_message": "",
        "requirements_complete": False,
        "requirements": None,
    }


# Build graph with tool execution support
graph = StateGraph(RequirementsGraphState)
graph.add_node("requirements_agent", requirements_agent_node)
graph.add_node("tools", tool_node)  # ToolNode handles tool execution automatically
graph.add_node("ask_user_for_info", ask_user_for_info)

# Routing
graph.add_edge(START, "requirements_agent")

# After agent, route based on tool calls and completion status
graph.add_conditional_edges(
    "requirements_agent",
    route_after_agent,
    {
        "tools": "tools",  # Execute tools
        "ask_user_for_info": "ask_user_for_info",  # Need more info from user
        END: END,  # Requirements complete
    },
)

# After tools execute, loop back to agent
graph.add_edge("tools", "requirements_agent")

# After asking user, loop back to agent
graph.add_edge("ask_user_for_info", "requirements_agent")

compiled_graph = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    initial_state = RequirementsGraphState(
        messages=[
            HumanMessage(
                content="I want to go to Seoul(ICN) from Tokyo(NRT). My dates are flexible."
            )
        ]
    )

    config = {"configurable": {"thread_id": "thread-1"}}

    result = compiled_graph.invoke(initial_state, config)

    while True:
        if "__interrupt__" in result:
            print(result["__interrupt__"])

            user_input = input("")

            current_state = Command(resume=user_input)

            result = compiled_graph.invoke(current_state, config)
        else:
            break

    print(result["requirements"])
