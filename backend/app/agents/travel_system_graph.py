import json
from typing import Optional

from langchain.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt
from langchain_core.runnables import RunnableConfig

from app.agents.requirements_graph import compiled_graph as requirements_graph
from app.agents.travel_system_agents import planner_agent, booker_agent
from app.agents.requirements_graph import RequirementsGraphState


checkpointer = InMemorySaver()


class TravelSystemState(MessagesState):
    """State for the full travel planning pipeline."""

    requirements: Optional[dict]  # CompleteRequirements dict from requirements graph
    itinerary: Optional[dict]  # Itinerary dict from planner agent
    bookings: Optional[dict]  # Bookings dict from booker agent


def requirements_subgraph_node(
    state: TravelSystemState, config: RunnableConfig
) -> TravelSystemState:
    """
    Invoke the requirements graph as a subgraph.
    The subgraph shares 'messages' and 'requirements' state with parent.

    Propagates interrupts to the top-level graph so the API can handle them.
    When resuming from an interrupt, resumes the subgraph with user input.
    """
    # Extract parent's thread_id from config and derive subgraph thread_id
    # RunnableConfig is dict-like with "configurable" key containing thread_id
    configurable = config.get("configurable", {}) if config else {}
    parent_thread_id = configurable.get("thread_id", "main-thread")
    subgraph_thread_id = f"{parent_thread_id}-requirements"
    subgraph_config = {"configurable": {"thread_id": subgraph_thread_id}}

    # Check if we have a pending interrupt by trying to get resume value
    # If we're resuming, the previous interrupt() call will return the resume value
    # We need to structure this so we can capture it
    # First, try normal invocation
    subgraph_state = RequirementsGraphState(
        messages=state["messages"],
        requirements_complete=False,
        interruption_message="",
        requirements=state.get("requirements"),
    )
    
    subgraph_result = requirements_graph.invoke(
        subgraph_state,
        subgraph_config,
    )

    # Check if subgraph has an interrupt - propagate it to top level
    if "__interrupt__" in subgraph_result:
        # Extract interrupt message
        interrupt_value = subgraph_result["__interrupt__"]
        if isinstance(interrupt_value, list) and len(interrupt_value) > 0:
            # Extract the interrupt value - could be a dict or string
            interrupt_obj = interrupt_value[0]
            if hasattr(interrupt_obj, "value"):
                interrupt_message = str(interrupt_obj.value)
            else:
                interrupt_message = str(interrupt_obj)
        else:
            interrupt_message = str(interrupt_value)

        # Propagate interrupt to top-level graph using interrupt()
        # This will pause the top-level graph and return the interrupt to the API
        # When resumed, interrupt() will return the resume value
        user_response = interrupt(interrupt_message)
        
        # If we get here, we're resuming - resume the subgraph with user response
        subgraph_result = requirements_graph.invoke(
            Command(resume=user_response),
            subgraph_config,
        )
        
        # Check again for interrupts (subgraph might need more info)
        if "__interrupt__" in subgraph_result:
            interrupt_value = subgraph_result["__interrupt__"]
            if isinstance(interrupt_value, list) and len(interrupt_value) > 0:
                interrupt_obj = interrupt_value[0]
                if hasattr(interrupt_obj, "value"):
                    interrupt_message = str(interrupt_obj.value)
                else:
                    interrupt_message = str(interrupt_obj)
            else:
                interrupt_message = str(interrupt_value)
            
            # Propagate the new interrupt
            interrupt(interrupt_message)

    # No interrupt, execution completed - extract requirements
    requirements = subgraph_result.get("requirements")

    # Generate conversational summary from requirements
    if requirements:
        origin = requirements.get('trip', {}).get('origin', {}).get('city', 'your origin')
        destination = requirements.get('trip', {}).get('destination', {}).get('city', 'your destination')
        summary = f"Perfect! I've gathered your travel requirements for a trip from {origin} to {destination}. Let me create an itinerary for you..."
    else:
        summary = "I've gathered your travel requirements. Let me create an itinerary for you..."

    # The result contains 'requirements' field populated when complete
    return {
        "messages": [AIMessage(content=summary, name="requirements")],
        "requirements": requirements,
        "itinerary": None,
        "bookings": None,
    }


def planner_agent_node(state: TravelSystemState) -> TravelSystemState:
    """
    Invoke planner agent to create itinerary based on requirements.
    """
    requirements = state.get("requirements")

    # Format requirements into context message for planner
    requirements_str = json.dumps(requirements, indent=2)
    planner_prompt = f"""Based on the following travel requirements, create a day-by-day itinerary:
    
{requirements_str}"""

    # Invoke planner agent
    response = planner_agent.invoke(
        {"messages": [HumanMessage(content=planner_prompt)]}
    )

    itinerary = response["structured_response"].itinerary.model_dump()

    # Generate conversational summary
    num_days = len(itinerary.get('days', []))
    if num_days > 0:
        summary = f"Great! I've created a {num_days}-day itinerary for you. Now let me book your flights and accommodations..."
    else:
        summary = "I've created your itinerary. Now let me book your flights and accommodations..."

    return {
        "messages": [AIMessage(content=summary, name="planner")],
        "requirements": requirements,
        "itinerary": itinerary,
        "bookings": None,
    }


def booker_agent_node(state: TravelSystemState) -> TravelSystemState:
    """
    Invoke booker agent to book flights and hotels based on requirements and itinerary.
    """
    requirements = state.get("requirements")
    itinerary = state.get("itinerary")

    # Format booking context
    requirements_str = json.dumps(requirements, indent=2)
    itinerary_str = json.dumps(itinerary, indent=2)

    booker_prompt = f"""Based on the following requirements and itinerary, book the flights and hotels:

REQUIREMENTS:
{requirements_str}

ITINERARY:
{itinerary_str}

Extract the flight ID from the confirmed flight in requirements and book it.
For hotels, use the destination city and dates from the itinerary or requirements to book a hotel.
Return booking confirmations for both flight and hotel."""

    # Invoke booker agent
    response = booker_agent.invoke({"messages": [HumanMessage(content=booker_prompt)]})

    # Extract structured bookings from response
    bookings = response["structured_response"].bookings.model_dump()

    # Generate conversational confirmation
    summary = "Perfect! I've completed your bookings."

    if bookings.get('flights'):
        flight_ref = bookings['flights'].get('reservation_ref', 'N/A')
        summary += f" Your flight is confirmed (Reference: {flight_ref})."

    if bookings.get('hotels'):
        hotel_ref = bookings['hotels'].get('reservation_ref', 'N/A')
        summary += f" Your hotel reservation is also confirmed (Reference: {hotel_ref})."

    summary += " All details are shown below. Have a wonderful trip!"

    return {
        "messages": [AIMessage(content=summary, name="booker")],
        "requirements": requirements,
        "itinerary": itinerary,
        "bookings": bookings,
    }


# Build the graph
graph = StateGraph(TravelSystemState)

graph.add_node("requirements_subgraph", requirements_subgraph_node)
graph.add_node("planner", planner_agent_node)
graph.add_node("booker", booker_agent_node)

# Define flow
graph.add_edge(START, "requirements_subgraph")
graph.add_edge("requirements_subgraph", "planner")
graph.add_edge("planner", "booker")
graph.add_edge("booker", END)

# Compile the graph
travel_system_graph = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    initial_state = TravelSystemState(
        messages=[
            HumanMessage(
                content="I want to go to Seoul(ICN) from Tokyo(NRT). My dates are flexible."
            )
        ],
        requirements=None,
        itinerary=None,
        bookings=None,
    )

    config = {"configurable": {"thread_id": "thread-1"}}

    # Invoke the graph - interrupt loop is now handled inside requirements_subgraph_node
    result = travel_system_graph.invoke(initial_state, config)

    print("\n=== FINAL RESULTS ===")
    print(f"Requirements: {json.dumps(result.get('requirements'), indent=2)}")
    print(f"\nItinerary: {json.dumps(result.get('itinerary'), indent=2)}")
    print(f"\nBookings: {json.dumps(result.get('bookings'), indent=2)}")
