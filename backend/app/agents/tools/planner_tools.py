# app/agents/tools/planner_tools.py
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool


# Base DuckDuckGo search tool
_base_web_search = DuckDuckGoSearchRun(
    name="web_search_base",
    description="Search the web for travel information, attractions, points of interest (POIs), and activities in a destination city. Use this to find popular sights, cultural sites, restaurants, shopping areas, and other tourist attractions.",
)


# Wrapper with logging for the web_search tool
@tool("web_search")
def web_search(query: str) -> str:
    """
    Search the web for travel information, attractions, points of interest (POIs), and activities in a destination city.
    Use this to find popular sights, cultural sites, restaurants, shopping areas, and other tourist attractions.
    """
    # TOOL ENTRY LOG
    print(f"\n[WEB_SEARCH_TOOL] ===== TOOL START =====")
    print(f"[WEB_SEARCH_TOOL] Input parameters:")
    print(f"[WEB_SEARCH_TOOL]   query: {query}")

    try:
        # Call the base DuckDuckGo search
        result = _base_web_search.run(query)

        # TOOL EXIT LOG - Success case
        result_lines = result.split('\n') if result else []
        result_preview = '\n'.join(result_lines[:3]) if result_lines else "No results"

        print(f"[WEB_SEARCH_TOOL] Search completed successfully")
        print(f"[WEB_SEARCH_TOOL] Result preview (first 3 lines):")
        for line in result_lines[:3]:
            if line.strip():
                print(f"[WEB_SEARCH_TOOL]   {line[:100]}")
        print(f"[WEB_SEARCH_TOOL] Total result length: {len(result)} characters")
        print(f"[WEB_SEARCH_TOOL] ===== TOOL COMPLETE =====\n")

        return result

    except Exception as e:
        print(f"[WEB_SEARCH_TOOL] Error during search: {e}")
        error_result = f"Search error: {str(e)}"
        print(f"[WEB_SEARCH_TOOL] ===== TOOL COMPLETE (ERROR) =====\n")
        return error_result
