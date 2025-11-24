# app/tools/flight_tools.py
import requests

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.config import settings


class FlightSearchInput(BaseModel):
    """Input schema for flight search requests."""

    origin: str = Field(
        ..., description="The IATA code for the origin airport"
    )
    destination: str = Field(
        ..., description="The IATA code for the destination airport"
    )


@tool("search_flight_availability", args_schema=FlightSearchInput)
def search_flight_availability(origin: str, destination: str) -> dict:
    """
    Checks if flights are available on a given date between two airports.
    Returns a small list of candidate options sorted by price.
    Only call this after you have the origin, destination, and date.
    """
    # TOOL ENTRY LOG
    print(f"\n[FLIGHT_SEARCH_TOOL] ===== TOOL START =====")
    print(f"[FLIGHT_SEARCH_TOOL] Input parameters:")
    print(f"[FLIGHT_SEARCH_TOOL]   origin: {origin}")
    print(f"[FLIGHT_SEARCH_TOOL]   destination: {destination}")

    api_url = f"{settings.CONVEX_BASE_URL}/flights/search"
    params = {"origin": origin, "destination": destination}

    try:
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()  # Raises an exception for 4XX/5XX errors

        flights = response.json().get("flights", [])

        # TOOL EXIT LOG - Success case
        result = None
        if not flights:
            result = {"available": False, "options": []}
            print(f"[FLIGHT_SEARCH_TOOL] No flights available")
        else:
            result = {"available": True, "options": flights}
            print(f"[FLIGHT_SEARCH_TOOL] Flights found: {len(flights)} option(s)")
            for idx, flight in enumerate(flights[:3]):  # Log first 3 flights
                print(f"[FLIGHT_SEARCH_TOOL]   Option {idx+1}: {flight.get('id', 'N/A')} - ${flight.get('price', 'N/A')}")

        print(f"[FLIGHT_SEARCH_TOOL] ===== TOOL COMPLETE =====\n")
        return result

    except requests.exceptions.RequestException as e:
        print(f"[FLIGHT_SEARCH_TOOL] API call failed: {e}")
        result = {"available": False, "options": [], "error": str(e)}
        print(f"[FLIGHT_SEARCH_TOOL] ===== TOOL COMPLETE (ERROR) =====\n")
        return result
    except Exception as e:
        print(f"[FLIGHT_SEARCH_TOOL] An unexpected error occurred: {e}")
        result = {
            "available": False,
            "options": [],
            "error": "An internal error occurred.",
        }
        print(f"[FLIGHT_SEARCH_TOOL] ===== TOOL COMPLETE (ERROR) =====\n")
        return result
