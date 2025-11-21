"""
Unit tests for the LangGraphToVercelAdapter.

These tests demonstrate how to test the adapter without needing a real LLM.
"""

import pytest
from unittest.mock import AsyncMock, Mock
from langchain.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState, START, END

from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter, stream_langgraph_to_vercel
from app.utils.message_extractors import default_message_extractor, structured_data_extractor


# Test fixtures
class TestGraphState(MessagesState):
    """Simple test state for mocking."""
    result: dict = None


def simple_agent_node(state: TestGraphState) -> TestGraphState:
    """Mock agent node that returns a simple message."""
    return {
        "messages": [AIMessage(content="Hello from agent")],
        "result": {"status": "success"}
    }


@pytest.fixture
def simple_graph():
    """Create a simple test graph."""
    graph = StateGraph(TestGraphState)
    graph.add_node("agent", simple_agent_node)
    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)
    return graph.compile()


@pytest.fixture
def adapter():
    """Create a basic adapter instance."""
    return LangGraphToVercelAdapter()


# Tests for message extractors
def test_default_message_extractor():
    """Test default extractor gets last message content."""
    state = {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="World"),
        ]
    }

    result = default_message_extractor(state)
    assert result == "World"


def test_default_message_extractor_empty_state():
    """Test default extractor handles empty state."""
    state = {"messages": []}
    result = default_message_extractor(state)
    assert result == ""


def test_structured_data_extractor():
    """Test structured data extractor gets from custom field."""
    extractor = structured_data_extractor("results")
    state = {
        "results": {"flight": "ABC123", "hotel": "XYZ789"}
    }

    result = extractor(state)
    assert "ABC123" in result
    assert "XYZ789" in result


# Tests for adapter
def test_adapter_initialization():
    """Test adapter can be initialized with defaults."""
    adapter = LangGraphToVercelAdapter()
    assert adapter.message_extractor is not None
    assert adapter.include_reasoning == False


def test_adapter_custom_extractor():
    """Test adapter accepts custom message extractor."""
    custom_extractor = lambda state: "custom message"
    adapter = LangGraphToVercelAdapter(message_extractor=custom_extractor)

    test_state = {"anything": "value"}
    result = adapter.message_extractor(test_state)
    assert result == "custom message"


def test_format_sse_event():
    """Test SSE event formatting."""
    adapter = LangGraphToVercelAdapter()
    data = {"type": "text-delta", "delta": "Hello"}

    result = adapter._format_sse_event(data)
    assert result.startswith("data: ")
    assert '"type":"text-delta"' in result
    assert '"delta":"Hello"' in result
    assert result.endswith("\n\n")


def test_create_message_id():
    """Test message ID creation."""
    adapter = LangGraphToVercelAdapter()
    msg_id = adapter._create_message_id()

    assert msg_id.startswith("msg_")
    assert len(msg_id) > 10  # Should include timestamp and unique ID


@pytest.mark.asyncio
async def test_adapter_stream_basic(simple_graph):
    """Test basic streaming with simple graph."""
    adapter = LangGraphToVercelAdapter()
    initial_state = {"messages": [HumanMessage(content="Test")]}
    config = {"configurable": {"thread_id": "test-123"}}

    events = []
    async for event in adapter.stream(simple_graph, initial_state, config):
        events.append(event)

    # Should have at least a start event
    assert len(events) > 0
    assert 'data: {"type":"start"' in events[0]


@pytest.mark.asyncio
async def test_convenience_function(simple_graph):
    """Test the convenience stream function."""
    initial_state = {"messages": [HumanMessage(content="Test")]}
    config = {"configurable": {"thread_id": "test-456"}}

    events = []
    async for event in stream_langgraph_to_vercel(simple_graph, initial_state, config):
        events.append(event)

    assert len(events) > 0


# Integration-style tests
@pytest.mark.asyncio
async def test_adapter_with_custom_extractor(simple_graph):
    """Test adapter with custom message extractor."""
    def custom_extractor(state):
        # Extract from result field instead of messages
        if "result" in state and state["result"]:
            return f"Status: {state['result'].get('status', 'unknown')}"
        return ""

    adapter = LangGraphToVercelAdapter(message_extractor=custom_extractor)
    initial_state = {"messages": [HumanMessage(content="Test")]}
    config = {"configurable": {"thread_id": "test-789"}}

    events = []
    async for event in adapter.stream(simple_graph, initial_state, config):
        events.append(event)

    # Should have events (exact content depends on custom extractor)
    assert len(events) > 0


# Edge case tests
def test_extractor_handles_dict_messages():
    """Test extractor handles both BaseMessage and dict messages."""
    # Dict representation
    state_dict = {
        "messages": [{"role": "ai", "content": "Hello dict"}]
    }
    result = default_message_extractor(state_dict)
    assert result == "Hello dict"

    # BaseMessage object
    state_obj = {
        "messages": [AIMessage(content="Hello object")]
    }
    result = default_message_extractor(state_obj)
    assert result == "Hello object"


def test_extractor_handles_none_state():
    """Test extractor handles missing fields gracefully."""
    state = {}  # No messages field
    result = default_message_extractor(state)
    assert result == ""


# Future test ideas (to implement):
# - Test interrupt handling
# - Test tool call streaming
# - Test error handling
# - Test with real LangGraph graphs
# - Test message chunking/streaming
# - Test concurrent streams
