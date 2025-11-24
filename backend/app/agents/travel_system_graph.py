import json
from typing import Optional

from langchain.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.requirements_graph import compiled_graph as requirements_graph
from app.agents.planner_graph import compiled_graph as planner_graph
from app.agents.booker_graph import compiled_graph as booker_graph


checkpointer = InMemorySaver()


class TravelSystemState(MessagesState):
    """State for the full travel planning pipeline."""

    requirements: Optional[dict]  # CompleteRequirements dict from requirements graph
    itinerary: Optional[dict]  # Itinerary dict from planner agent
    bookings: Optional[dict]  # Bookings dict from booker agent


def add_requirements_summary(state: TravelSystemState) -> TravelSystemState:
    """Add a conversational summary after requirements are gathered."""
    requirements = state.get("requirements")

    if requirements:
        origin = requirements.get('trip', {}).get('origin', {}).get('city', 'your origin')
        destination = requirements.get('trip', {}).get('destination', {}).get('city', 'your destination')
        summary = f"Perfect! I've gathered your travel requirements for a trip from {origin} to {destination}. Let me create an itinerary for you..."
    else:
        summary = "I've gathered your travel requirements. Let me create an itinerary for you..."

    return {"messages": [AIMessage(content=summary, name="requirements")]}


def prepare_planner_input(state: TravelSystemState) -> TravelSystemState:
    """Format requirements into a prompt for the planner agent."""
    requirements = state.get("requirements")
    requirements_str = json.dumps(requirements, indent=2)
    planner_prompt = f"""Based on the following travel requirements, create a day-by-day itinerary:

{requirements_str}"""

    return {"messages": [HumanMessage(content=planner_prompt)]}


def add_planner_summary(state: TravelSystemState) -> TravelSystemState:
    """Add a conversational summary after itinerary is created."""
    itinerary = state.get("itinerary")
    num_days = len(itinerary.get('days', [])) if itinerary else 0

    if num_days > 0:
        summary = f"Great! I've created a {num_days}-day itinerary for you. Now let me book your flights and accommodations..."
    else:
        summary = "I've created your itinerary. Now let me book your flights and accommodations..."

    return {"messages": [AIMessage(content=summary, name="planner")]}


def prepare_booker_input(state: TravelSystemState) -> TravelSystemState:
    """Format requirements and itinerary into a prompt for the booker agent."""
    requirements = state.get("requirements")
    itinerary = state.get("itinerary")

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

    return {"messages": [HumanMessage(content=booker_prompt)]}


def add_booker_summary(state: TravelSystemState) -> TravelSystemState:
    """Add a conversational summary after bookings are complete."""
    bookings = state.get("bookings")

    summary = "Perfect! I've completed your bookings."

    if bookings and bookings.get('flights'):
        flight_ref = bookings['flights'].get('reservation_ref', 'N/A')
        summary += f" Your flight is confirmed (Reference: {flight_ref})."

    if bookings and bookings.get('hotels'):
        hotel_ref = bookings['hotels'].get('reservation_ref', 'N/A')
        summary += f" Your hotel reservation is also confirmed (Reference: {hotel_ref})."

    summary += " All details are shown below. Have a wonderful trip!"

    return {"messages": [AIMessage(content=summary, name="booker")]}


# Build the graph using native LangGraph pattern
# Add compiled subgraphs DIRECTLY as nodes for automatic event streaming with subgraphs=True
graph = StateGraph(TravelSystemState)

# Add subgraphs directly (native pattern for streaming with subgraphs=True)
graph.add_node("requirements", requirements_graph)
graph.add_node("planner", planner_graph)
graph.add_node("booker", booker_graph)

# Add helper nodes for summaries and input preparation
graph.add_node("add_requirements_summary", add_requirements_summary)
graph.add_node("prepare_planner_input", prepare_planner_input)
graph.add_node("add_planner_summary", add_planner_summary)
graph.add_node("prepare_booker_input", prepare_booker_input)
graph.add_node("add_booker_summary", add_booker_summary)

# Define flow: subgraph -> summary -> prepare input -> next subgraph -> ...
graph.add_edge(START, "requirements")
graph.add_edge("requirements", "add_requirements_summary")
graph.add_edge("add_requirements_summary", "prepare_planner_input")
graph.add_edge("prepare_planner_input", "planner")
graph.add_edge("planner", "add_planner_summary")
graph.add_edge("add_planner_summary", "prepare_booker_input")
graph.add_edge("prepare_booker_input", "booker")
graph.add_edge("booker", "add_booker_summary")
graph.add_edge("add_booker_summary", END)

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
