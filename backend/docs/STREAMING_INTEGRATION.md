# LangGraph to Vercel Streaming Integration Guide

This guide explains how to integrate any LangGraph-based agent system with Vercel AI SDK's Data Stream Protocol using our pluggable adapter layer.

## Philosophy: Separation of Concerns

```
┌──────────────────────────────────────────────────┐
│  Core Agentic Logic (LangGraph)                  │
│  - Agent definitions, tools, prompts             │
│  - Graph structure and flow                      │
│  - Business logic                                │
│  ✅ NEVER needs to know about streaming          │
└────────────────────┬─────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────┐
│  Adapter Layer (Pluggable)                       │
│  - Transforms LangGraph events → Vercel protocol │
│  - Configurable message extraction               │
│  - No graph modifications required               │
└────────────────────┬─────────────────────────────┘
                     │
                     ↓
┌──────────────────────────────────────────────────┐
│  Vercel Data Stream Protocol (SSE)               │
│  - Standard format for frontend hooks            │
│  - Works with useChat, useAssistant, etc.        │
└──────────────────────────────────────────────────┘
```

## Minimal Standard Contract

For your LangGraph graph to work with the streaming adapter, follow these simple rules:

### 1. Extend MessagesState

```python
from langgraph.graph import StateGraph, MessagesState

class MyGraphState(MessagesState):
    """
    MessagesState provides the 'messages' field automatically.
    Add your custom fields below.
    """
    my_custom_data: Optional[dict] = None
    results: Optional[dict] = None
```

**Why?** The adapter extracts conversational text from the `messages` array.

### 2. Return AIMessage Objects

```python
from langchain.messages import AIMessage

def my_agent_node(state: MyGraphState) -> MyGraphState:
    # Your agent logic here...
    result = my_agent.invoke({"messages": state["messages"]})

    return {
        "messages": [AIMessage(content="Processing complete!")],  # ← For UI
        "my_custom_data": {"status": "done"}  # ← For state
    }
```

**That's it!** No other requirements.

---

## Quick Start

### Basic Usage

```python
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

async def my_api_endpoint(request):
    # Your graph setup
    initial_state = {"messages": [HumanMessage(content=user_input)]}
    config = {"configurable": {"thread_id": "user-123"}}

    # Stream using the adapter
    async for sse_event in stream_langgraph_to_vercel(
        graph=my_compiled_graph,
        initial_state=initial_state,
        config=config
    ):
        yield sse_event
```

### Custom Message Extraction

If your graph stores conversational text in a custom field:

```python
from app.utils.message_extractors import structured_data_extractor
from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter

# Create extractor for custom field
my_extractor = structured_data_extractor("summary")

# Use adapter with custom extractor
adapter = LangGraphToVercelAdapter(message_extractor=my_extractor)

async for event in adapter.stream(my_graph, initial_state, config):
    yield event
```

### Fallback Strategy

Use multiple extractors with fallback:

```python
from app.utils.message_extractors import MessageExtractorChain, summary_field_extractor, default_message_extractor

# Try summary field first, fallback to messages
chain = MessageExtractorChain([
    summary_field_extractor,
    default_message_extractor,
])

adapter = LangGraphToVercelAdapter(message_extractor=chain.extract)
```

---

## Advanced Patterns

### Pattern 1: Multi-Agent Workflow

```python
from langgraph.graph import StateGraph, MessagesState

class WorkflowState(MessagesState):
    step_1_result: Optional[dict] = None
    step_2_result: Optional[dict] = None
    step_3_result: Optional[dict] = None

def agent_1(state):
    result = process_step_1(state)
    return {
        "messages": [AIMessage(content="Step 1 complete")],
        "step_1_result": result
    }

def agent_2(state):
    result = process_step_2(state["step_1_result"])
    return {
        "messages": [AIMessage(content="Step 2 complete")],
        "step_2_result": result
    }

# Build graph
graph = StateGraph(WorkflowState)
graph.add_node("agent_1", agent_1)
graph.add_node("agent_2", agent_2)
graph.add_edge(START, "agent_1")
graph.add_edge("agent_1", "agent_2")
graph.add_edge("agent_2", END)

compiled_graph = graph.compile()

# Stream it - no changes needed!
async for event in stream_langgraph_to_vercel(compiled_graph, initial_state, config):
    yield event
```

### Pattern 2: Human-in-the-Loop (Interrupts)

```python
from langgraph.types import interrupt

def requirements_agent(state):
    if missing_info:
        # Trigger interrupt
        user_response = interrupt("What's your budget?")

        # Continue after user responds
        return {
            "messages": [HumanMessage(content=user_response)],
            "requirements_complete": False
        }

    return {
        "messages": [AIMessage(content="Requirements gathered!")],
        "requirements_complete": True
    }

# The adapter automatically handles interrupts!
# Frontend receives:
# data: {"type":"finish","finishReason":"interrupt","interruptMessage":"What's your budget?"}
```

### Pattern 3: Structured Data Streaming

Send custom data alongside messages:

```python
def booking_agent(state):
    booking_result = book_flight_and_hotel(state)

    return {
        "messages": [AIMessage(content="Booking complete!")],
        "booking_data": booking_result  # ← Custom structured data
    }

# In your API endpoint:
async def stream_with_data(graph, initial_state, config):
    final_state = None

    # Stream events
    async for event in stream_langgraph_to_vercel(graph, initial_state, config):
        yield event

        # Capture final state
        if "booking_data" in event:
            final_state = event

    # Send custom data event after streaming completes
    if final_state and "booking_data" in final_state:
        yield f'data: {json.dumps({
            "type": "data-booking",
            "data": final_state["booking_data"]
        })}\n\n'
```

---

## Message Extraction Strategies

The adapter provides flexible ways to extract conversational text from your state.

### Strategy 1: Default (Messages Array)

```python
# Automatically extracts from state["messages"][-1].content
adapter = LangGraphToVercelAdapter()  # Uses default_message_extractor
```

### Strategy 2: Custom Field

```python
from app.utils.message_extractors import structured_data_extractor

# Extract from state["summary"] instead
extractor = structured_data_extractor("summary")
adapter = LangGraphToVercelAdapter(message_extractor=extractor)
```

### Strategy 3: Multi-Field

```python
from app.utils.message_extractors import multi_field_extractor

# Combine multiple fields
extractor = multi_field_extractor(["requirements", "itinerary"], separator="\n\n")
adapter = LangGraphToVercelAdapter(message_extractor=extractor)
```

### Strategy 4: Custom Logic

```python
def my_custom_extractor(state: dict) -> str:
    """Your custom extraction logic."""
    if "error" in state:
        return f"Error: {state['error']}"
    elif "summary" in state:
        return state["summary"]
    else:
        # Fallback to messages
        messages = state.get("messages", [])
        return messages[-1].content if messages else ""

adapter = LangGraphToVercelAdapter(message_extractor=my_custom_extractor)
```

---

## Comparison: Old vs. New Approach

### Old Approach (Tightly Coupled)

```python
# In vercel_stream.py - hardcoded logic for specific graph
async def stream_langgraph_to_vercel(graph, state, config):
    # ... lots of graph-specific logic ...

    # Hardcoded field checks
    if "requirements" in final_state:
        yield format_sse({"type": "data-requirements", ...})

    if "itinerary" in final_state:
        yield format_sse({"type": "data-itinerary", ...})
```

**Problems:**
- ❌ Coupled to specific graph structure
- ❌ Can't reuse with different graphs
- ❌ Hard to customize message extraction
- ❌ Changes to graph require changes to streaming

### New Approach (Pluggable)

```python
# In your API - clean separation
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

async def stream_any_graph(graph, state, config):
    # Works with ANY graph!
    async for event in stream_langgraph_to_vercel(graph, state, config):
        yield event
```

**Benefits:**
- ✅ Works with any LangGraph graph
- ✅ Configurable message extraction
- ✅ No coupling to graph structure
- ✅ Change graph without touching streaming

---

## Frontend Integration

The streamed events work seamlessly with Vercel AI SDK hooks:

```typescript
// Frontend (Next.js/React)
import { useChat } from 'ai/react';

export default function ChatInterface() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: '/api/chat',  // Your FastAPI endpoint
  });

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>
          <strong>{m.role}:</strong> {m.content}
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
```

The adapter automatically formats events so they work with `useChat`, `useAssistant`, and other Vercel hooks!

---

## Best Practices

### 1. Keep Core Logic Pure

```python
# ✅ Good: Agent knows nothing about streaming
def my_agent(state):
    result = do_agent_work(state)
    return {
        "messages": [AIMessage(content="Done!")],
        "result": result
    }

# ❌ Bad: Agent coupled to streaming protocol
def my_agent(state):
    result = do_agent_work(state)
    # Don't do this!
    yield format_sse({"type": "text-delta", ...})
```

### 2. Use Structured State

```python
# ✅ Good: Clear, typed state
class MyState(MessagesState):
    requirements: Optional[RequirementsModel] = None
    itinerary: Optional[ItineraryModel] = None

# ❌ Bad: Untyped dict soup
class MyState(MessagesState):
    data: dict = {}
```

### 3. Consistent Message Pattern

```python
# ✅ Good: Always return AIMessage for conversational text
return {
    "messages": [AIMessage(content="User-friendly message")],
    "structured_data": {...}
}

# ❌ Bad: Inconsistent message handling
return {
    "messages": "Sometimes string, sometimes AIMessage",
    "data": {...}
}
```

---

## Troubleshooting

### No Text Appearing in Frontend

**Problem:** Frontend shows nothing

**Solution:** Ensure your nodes return `AIMessage` objects:

```python
# Add this to your nodes
return {
    "messages": [AIMessage(content="Your message here")],
    # ... other state fields
}
```

### Interrupts Not Working

**Problem:** Graph interrupts but frontend doesn't handle it

**Solution:** The adapter automatically converts interrupts. Check your frontend:

```typescript
const { messages, isLoading } = useChat({
  api: '/api/chat',
  onFinish: (message, { finishReason }) => {
    if (finishReason === 'interrupt') {
      // Handle interrupt
      console.log('Agent needs more info');
    }
  }
});
```

### Custom Data Not Streaming

**Problem:** Want to send custom structured data

**Solution:** Extend the adapter or send data events after streaming:

```python
# After the main stream completes, send custom data
async for event in stream_langgraph_to_vercel(graph, state, config):
    yield event

# Then send your custom data
yield f'data: {json.dumps({"type": "data-custom", "data": my_data})}\n\n'
```

---

## Migration Guide

### From Old vercel_stream.py to New Adapter

**Before:**
```python
from app.utils.vercel_stream import stream_langgraph_to_vercel as old_stream

async for event in old_stream(graph, state, config, stream_mode="messages"):
    yield event
```

**After:**
```python
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

async for event in stream_langgraph_to_vercel(graph, state, config):
    yield event
```

**Changes needed:** None! Just update the import.

---

## Summary

The LangGraph to Vercel adapter provides:

1. **Clean Separation**: Core logic ← → Adapter ← → Protocol
2. **Pluggable Design**: Works with any compliant LangGraph graph
3. **Minimal Contract**: Just extend `MessagesState` and return `AIMessage`
4. **Flexible Extraction**: Customize how messages are extracted from state
5. **Zero Coupling**: Change your graph without touching streaming code

**Bottom Line:** Build your agents however you want. The adapter handles the rest.
