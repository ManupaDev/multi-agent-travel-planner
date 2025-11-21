# LangGraph to Vercel Streaming Adapter

## Overview

This project introduces a **pluggable streaming adapter** that cleanly separates LangGraph's agentic logic from Vercel's Data Stream Protocol. This allows any LangGraph-based agent system to stream to Vercel AI SDK frontends without modifying core agent code.

## The Problem We Solved

### Before: Tightly Coupled Streaming

```python
# vercel_stream.py - hardcoded for specific graph
async def stream_langgraph_to_vercel(graph, state, config):
    # ... lots of graph-specific logic ...

    # Hardcoded field checks
    if "requirements" in final_state:
        yield format_sse({"type": "data-requirements", ...})

    if "itinerary" in final_state:
        yield format_sse({"type": "data-itinerary", ...})
```

**Issues:**
- ❌ Coupled to specific graph structure (requirements, itinerary, bookings)
- ❌ Can't reuse with different LangGraph graphs
- ❌ Hard to customize message extraction
- ❌ Violates separation of concerns

### After: Pluggable Adapter

```python
# langgraph_vercel_adapter.py - works with ANY graph
async def stream_any_graph(graph, state, config):
    async for event in stream_langgraph_to_vercel(graph, state, config):
        yield event
```

**Benefits:**
- ✅ Works with ANY LangGraph graph
- ✅ Zero coupling to graph structure
- ✅ Pluggable message extraction
- ✅ Clean separation of concerns

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│  CORE AGENTIC LOGIC (LangGraph)                 │
│  - Agent definitions, tools, prompts            │
│  - Graph structure and workflow                 │
│  - Business logic                               │
│  ✅ Never needs to know about streaming         │
└────────────────────┬────────────────────────────┘
                     │ Standard Contract:
                     │ - Extend MessagesState
                     │ - Return AIMessage objects
                     ↓
┌─────────────────────────────────────────────────┐
│  ADAPTER LAYER (Pluggable)                      │
│  - LangGraphToVercelAdapter                     │
│  - Configurable message extractors              │
│  - Event mapping LangGraph → Vercel             │
│  ✅ No graph-specific code                      │
└────────────────────┬────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────┐
│  VERCEL DATA STREAM PROTOCOL (SSE)              │
│  - text-delta, tool-call, finish events         │
│  - Works with useChat, useAssistant hooks       │
│  ✅ Standard format                             │
└─────────────────────────────────────────────────┘
```

---

## Key Components

### 1. LangGraphToVercelAdapter

**File**: `app/utils/langgraph_vercel_adapter.py`

The core adapter class that transforms LangGraph events to Vercel SSE events.

```python
from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter

adapter = LangGraphToVercelAdapter(
    message_extractor=custom_extractor,  # Optional
    include_reasoning=False,             # Optional
)

async for sse_event in adapter.stream(graph, initial_state, config):
    yield sse_event
```

**Features:**
- Automatic event mapping (LangGraph → Vercel protocol)
- Configurable message extraction
- Interrupt handling (human-in-the-loop)
- Tool call streaming
- Error handling

### 2. Message Extractors

**File**: `app/utils/message_extractors.py`

Flexible strategies for extracting conversational text from LangGraph state.

**Built-in Extractors:**

```python
from app.utils.message_extractors import (
    default_message_extractor,        # Extract from messages[-1].content
    structured_data_extractor,        # Extract from custom field
    multi_field_extractor,            # Combine multiple fields
    summary_field_extractor,          # Extract from 'summary' field
    MessageExtractorChain,            # Chain multiple extractors
)

# Use default
adapter = LangGraphToVercelAdapter()

# Use custom field
extractor = structured_data_extractor("my_field")
adapter = LangGraphToVercelAdapter(message_extractor=extractor)

# Use fallback chain
chain = MessageExtractorChain([
    summary_field_extractor,
    default_message_extractor,
])
adapter = LangGraphToVercelAdapter(message_extractor=chain.extract)
```

### 3. Convenience Function

**File**: `app/utils/langgraph_vercel_adapter.py`

```python
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

# One-liner streaming
async for event in stream_langgraph_to_vercel(graph, initial_state, config):
    yield event
```

---

## Minimal Standard Contract

For any LangGraph graph to work with the adapter:

### Requirement 1: Extend MessagesState

```python
from langgraph.graph import MessagesState

class YourState(MessagesState):  # ← Must extend MessagesState
    # Your custom fields
    custom_data: Optional[dict] = None
```

### Requirement 2: Return AIMessage Objects

```python
from langchain.messages import AIMessage

def your_node(state):
    return {
        "messages": [AIMessage(content="User-friendly message")],
        "custom_data": {...}  # Optional structured data
    }
```

**That's it!** No other requirements.

---

## Usage Examples

### Example 1: Basic Streaming

```python
# app/api/services/my_service.py
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

async def stream_my_graph(message: str, thread_id: str):
    initial_state = {"messages": [HumanMessage(content=message)]}
    config = {"configurable": {"thread_id": thread_id}}

    async for event in stream_langgraph_to_vercel(
        graph=my_compiled_graph,
        initial_state=initial_state,
        config=config,
    ):
        yield event
```

### Example 2: Custom Extractor

```python
# Extract from custom 'summary' field
from app.utils.message_extractors import structured_data_extractor
from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter

extractor = structured_data_extractor("summary")
adapter = LangGraphToVercelAdapter(message_extractor=extractor)

async for event in adapter.stream(graph, initial_state, config):
    yield event
```

### Example 3: Travel System (Real Implementation)

**File**: `app/api/services/travel_system_streaming_service_v2.py`

```python
from app.agents.travel_system_graph import travel_system_graph, TravelSystemState
from app.utils.langgraph_vercel_adapter import stream_langgraph_to_vercel

async def stream_travel_system_chat_v2(message: str, thread_id: str):
    """Clean, decoupled streaming for travel planner."""
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = TravelSystemState(
        messages=[HumanMessage(content=message)],
        requirements=None,
        itinerary=None,
        bookings=None,
    )

    # Just works! No graph-specific code needed.
    async for event in stream_langgraph_to_vercel(
        graph=travel_system_graph,
        initial_state=initial_state,
        config=config,
    ):
        yield event
```

---

## Comparison: Old vs. New

| Aspect | Old (vercel_stream.py) | New (Adapter) |
|--------|------------------------|---------------|
| **Coupling** | Tightly coupled to travel graph | Zero coupling |
| **Reusability** | Only works with travel graph | Works with any graph |
| **Customization** | Hard-coded logic | Pluggable extractors |
| **Graph Changes** | Requires streaming code updates | No updates needed |
| **Separation** | Mixed concerns | Clean layers |
| **Testability** | Hard to mock | Easy to test |

---

## Files Created

### Core Adapter Layer
1. **`app/utils/langgraph_vercel_adapter.py`** (320 lines)
   - `LangGraphToVercelAdapter` class
   - Event mapping logic
   - Convenience functions

2. **`app/utils/message_extractors.py`** (220 lines)
   - Default extractors
   - Custom field extractors
   - Extractor chains
   - Fallback strategies

### Examples & Documentation
3. **`app/api/services/travel_system_streaming_service_v2.py`** (80 lines)
   - Real-world usage example
   - Custom extractor demo
   - Generic graph streaming

4. **`docs/STREAMING_INTEGRATION.md`** (600+ lines)
   - Complete integration guide
   - Patterns and best practices
   - Troubleshooting
   - Migration guide

### Tests
5. **`tests/test_langgraph_vercel_adapter.py`** (200+ lines)
   - Unit tests for adapter
   - Unit tests for extractors
   - Integration examples
   - Edge case handling

---

## Event Mapping

### LangGraph Events → Vercel SSE Events

| LangGraph Event | Vercel SSE Event | Purpose |
|----------------|------------------|---------|
| Graph start | `{"type":"start","messageId":"..."}` | Message initialization |
| AIMessage content | `{"type":"text-delta","delta":"..."}` | Streaming text |
| Tool execution start | `{"type":"tool-call","toolName":"..."}` | Tool invocation |
| Tool execution end | `{"type":"tool-result","result":"..."}` | Tool output |
| `__interrupt__` | `{"type":"finish","finishReason":"interrupt"}` | Human-in-the-loop |
| Graph completion | `{"type":"finish"}` | Done |
| Error | `{"type":"error","error":"..."}` | Error handling |

---

## Benefits of This Approach

### 1. **Clean Separation of Concerns**
- Core agent logic never knows about streaming
- Streaming layer never knows about business logic
- Each layer can evolve independently

### 2. **Reusability**
- Same adapter works for ANY LangGraph graph
- No need to write custom streaming logic per graph
- DRY principle in action

### 3. **Flexibility**
- Pluggable message extractors
- Configurable event handling
- Easy to extend for new features

### 4. **Maintainability**
- Changes to graphs don't affect streaming
- Changes to protocol don't affect graphs
- Clear responsibilities

### 5. **Testability**
- Easy to mock and test
- Unit tests for each component
- Integration tests with fake graphs

---

## Analogy to Vercel AI SDK's Pattern

This adapter follows the same philosophy as Vercel AI SDK:

### Vercel AI SDK (TypeScript)
```typescript
const result = streamText({
  model: openai('gpt-4o'),
  messages,
  tools: { searchWeb, bookFlight },
  stopWhen: stepCountIs(5),  // ← Multi-step control

  // Model generates own conversational responses
  // No manual string building!
})
```

### Our Adapter (Python)
```python
async for event in stream_langgraph_to_vercel(
    graph=my_graph,  # Any graph
    initial_state=initial_state,
    config=config,

    # Adapter handles message extraction
    # No manual formatting!
)
```

**Both approaches:**
- ✅ Separate core logic from presentation
- ✅ Pluggable/configurable
- ✅ Let the model (or agent) generate natural responses
- ✅ Standard protocol for frontends

---

## Next Steps

### For Users of This Adapter

1. **Read the integration guide**: `docs/STREAMING_INTEGRATION.md`
2. **Look at examples**: `app/api/services/travel_system_streaming_service_v2.py`
3. **Run tests**: `pytest tests/test_langgraph_vercel_adapter.py`
4. **Try with your graph**: Just ensure you follow the minimal contract!

### For Contributors

1. **Add more extractors**: Create new strategies in `message_extractors.py`
2. **Enhance event mapping**: Add support for more LangGraph event types
3. **Improve tests**: Add integration tests with real LangGraph graphs
4. **Extend documentation**: Add more real-world examples

---

## FAQ

**Q: Do I need to modify my existing LangGraph graph?**
A: No! As long as you extend `MessagesState` and return `AIMessage` objects, it works out of the box.

**Q: What if my graph stores messages in a custom field?**
A: Use a custom message extractor or the `structured_data_extractor` factory.

**Q: Can I still use the old streaming code?**
A: Yes! The old `vercel_stream.py` is untouched. The new adapter is an alternative, not a replacement.

**Q: Does this work with interrupts (human-in-the-loop)?**
A: Yes! The adapter automatically handles interrupts and formats them for Vercel protocol.

**Q: How do I send custom structured data?**
A: Your graph can return any fields in state. For UI display, ensure `messages` contains user-friendly text. For custom data events, you can extend the adapter or send them after streaming.

**Q: Is this production-ready?**
A: The adapter is functional and tested. For production, you may want to add more error handling, logging, and monitoring.

---

## Summary

We've created a **pluggable, reusable streaming adapter** that:

1. ✅ Works with ANY LangGraph graph (following minimal contract)
2. ✅ Provides clean separation between agentic logic and streaming protocol
3. ✅ Offers flexible, configurable message extraction
4. ✅ Handles interrupts, tool calls, and errors automatically
5. ✅ Follows Vercel Data Stream Protocol standard
6. ✅ Is well-documented and tested

**The Result:** You can build LangGraph agents however you want, and the adapter makes them work with Vercel AI SDK frontends—no coupling required.
