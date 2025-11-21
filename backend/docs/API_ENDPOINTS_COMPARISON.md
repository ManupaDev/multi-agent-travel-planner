# Travel System API Endpoints Comparison

This document compares the three available endpoints for the travel planning system and helps you choose the right one for your use case.

## Quick Reference

| Endpoint | Implementation | Status | Use Case |
|----------|---------------|--------|----------|
| `POST /chat` | Old adapter (tightly coupled) | ✅ Production | Existing integrations, proven stability |
| `POST /chat/v2` | New pluggable adapter | ✅ Production | New integrations, cleaner architecture |
| `POST /chat-sync` | Synchronous (no streaming) | ⚠️ Legacy | Backward compatibility only |

---

## Endpoint Details

### 1. `POST /api/travel-system/chat` (Original)

**Implementation:** `travel_system_streaming_service.py` + `vercel_stream.py`

**Architecture:**
```
Request → extract_user_message() → stream_travel_system_chat()
                                          ↓
                                   vercel_stream.py
                                   (tightly coupled)
                                          ↓
                                   Vercel SSE Protocol
```

**Characteristics:**
- ✅ **Production-proven** - Battle-tested implementation
- ✅ **Feature-complete** - All features working
- ❌ **Tightly coupled** - Hardcoded for travel planner graph
- ❌ **Less maintainable** - Graph changes may require streaming updates
- ❌ **Not reusable** - Can't use with other LangGraph graphs

**Code Example:**
```typescript
// Frontend (Next.js/React)
const { messages, input, handleSubmit } = useChat({
  api: '/api/travel-system/chat',  // Original endpoint
});
```

**Use When:**
- You need maximum stability
- You're maintaining existing integrations
- You don't need to customize streaming behavior

---

### 2. `POST /api/travel-system/chat/v2` (New - Recommended)

**Implementation:** `travel_system_streaming_service_v2.py` + `langgraph_vercel_adapter.py`

**Architecture:**
```
Request → extract_user_message() → stream_travel_system_chat_v2()
                                          ↓
                                   LangGraphToVercelAdapter
                                   (pluggable, reusable)
                                          ↓
                                   Vercel SSE Protocol
```

**Characteristics:**
- ✅ **Clean architecture** - Separation of concerns
- ✅ **Pluggable** - Works with ANY LangGraph graph
- ✅ **Maintainable** - Graph changes don't affect streaming
- ✅ **Testable** - Easy to mock and test
- ✅ **Customizable** - Pluggable message extractors
- ⚠️ **Newer** - Less battle-tested than v1

**Code Example:**
```typescript
// Frontend (Next.js/React)
const { messages, input, handleSubmit } = useChat({
  api: '/api/travel-system/chat/v2',  // New adapter endpoint
});
```

**Use When:**
- You're starting a new integration
- You value clean architecture
- You might want to customize message extraction
- You plan to reuse streaming with other graphs

---

### 3. `POST /api/travel-system/chat-sync` (Legacy)

**Implementation:** `travel_system_service.py` (synchronous)

**Architecture:**
```
Request → process_travel_system_chat()
              ↓
         Returns complete response
         (no streaming)
```

**Characteristics:**
- ⚠️ **Legacy only** - For backward compatibility
- ❌ **No streaming** - Waits for complete execution
- ❌ **Poor UX** - User sees nothing until done
- ❌ **Timeout risk** - Long-running tasks may timeout
- ✅ **Simple** - Easier to debug

**Code Example:**
```typescript
// Frontend (fetch)
const response = await fetch('/api/travel-system/chat-sync', {
  method: 'POST',
  body: JSON.stringify({ message, thread_id }),
});
const data = await response.json();
```

**Use When:**
- You need to support legacy clients
- You're debugging and want to see full response
- Your use case doesn't require real-time streaming

---

## Feature Comparison

| Feature | `/chat` (v1) | `/chat/v2` (New) | `/chat-sync` (Legacy) |
|---------|--------------|------------------|----------------------|
| **Streaming** | ✅ Yes | ✅ Yes | ❌ No |
| **Interrupts** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Real-time updates** | ✅ Yes | ✅ Yes | ❌ No |
| **Tool call visibility** | ✅ Yes | ✅ Yes | ❌ No |
| **Pluggable architecture** | ❌ No | ✅ Yes | N/A |
| **Reusable with other graphs** | ❌ No | ✅ Yes | ❌ No |
| **Custom message extraction** | ❌ Hard | ✅ Easy | N/A |
| **Production-tested** | ✅ High | ⚠️ Medium | ✅ High |
| **Code maintainability** | ⚠️ Medium | ✅ High | ✅ High |

---

## Request/Response Format

All three endpoints accept the same request format:

### Request (Vercel AI SDK Format)

```typescript
{
  "id": "conversation-abc123",           // Conversation ID
  "messages": [                          // Message history
    {
      "id": "msg-1",
      "role": "user",
      "parts": [
        { "type": "text", "text": "I want to go to Tokyo" }
      ]
    }
  ],
  "thread_id": "user-thread-456",        // Optional: explicit thread ID
  "trigger": "submit-message",           // UI trigger
  "resume": false                        // Whether resuming from interrupt
}
```

### Response

**Streaming Endpoints (`/chat` and `/chat/v2`):**

Server-Sent Events (SSE) format:

```
data: {"type":"start","messageId":"msg-abc123"}

data: {"type":"text-delta","id":"msg-abc123","delta":"Great!"}

data: {"type":"text-delta","id":"msg-abc123","delta":" I'll help"}

data: {"type":"finish"}

data: [DONE]
```

**Sync Endpoint (`/chat-sync`):**

JSON response:

```json
{
  "message": "I'll help you plan your trip to Tokyo...",
  "is_interrupt": false,
  "requirements": { ... },
  "itinerary": { ... },
  "bookings": { ... }
}
```

---

## Migration Guide

### From `/chat-sync` to `/chat/v2`

**Before (Synchronous):**
```typescript
const response = await fetch('/api/travel-system/chat-sync', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: userInput, thread_id: threadId })
});
const data = await response.json();
console.log(data.message);
```

**After (Streaming):**
```typescript
import { useChat } from 'ai/react';

function ChatInterface() {
  const { messages, input, handleInputChange, handleSubmit } = useChat({
    api: '/api/travel-system/chat/v2',
  });

  return (
    <div>
      {messages.map(m => (
        <div key={m.id}>{m.content}</div>
      ))}
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={handleInputChange} />
      </form>
    </div>
  );
}
```

### From `/chat` to `/chat/v2`

**Change one line:**
```typescript
const { messages } = useChat({
  api: '/api/travel-system/chat/v2',  // Just change the URL!
});
```

Everything else works identically!

---

## Performance Comparison

| Metric | `/chat` | `/chat/v2` | `/chat-sync` |
|--------|---------|------------|--------------|
| **Time to first token** | ~500ms | ~500ms | N/A (waits for completion) |
| **Total execution time** | 15-30s | 15-30s | 15-30s |
| **Perceived performance** | ✅ Excellent | ✅ Excellent | ❌ Poor |
| **Memory usage** | Low | Low | Medium |
| **Network overhead** | Minimal | Minimal | None |

---

## Architecture Benefits (v2 vs v1)

### Code Coupling

**V1 (`/chat`):**
```python
# vercel_stream.py - tightly coupled
if "requirements" in final_state:  # ← Hardcoded field
    yield format_sse({"type": "data-requirements", ...})

if "itinerary" in final_state:    # ← Hardcoded field
    yield format_sse({"type": "data-itinerary", ...})
```

**V2 (`/chat/v2`):**
```python
# langgraph_vercel_adapter.py - zero coupling
async for event in stream_langgraph_to_vercel(
    graph=any_graph,  # ← Works with ANY graph!
    initial_state=state,
    config=config,
)
```

### Reusability

**V1:** Only works with travel planner graph

**V2:** Works with ANY LangGraph graph:
```python
# Same adapter works for:
- Travel planner graph ✅
- Customer support graph ✅
- Document analysis graph ✅
- Any graph extending MessagesState ✅
```

### Customization

**V1:** Hard to customize - need to modify vercel_stream.py

**V2:** Easy - just provide custom extractor:
```python
from app.utils.message_extractors import structured_data_extractor
from app.utils.langgraph_vercel_adapter import LangGraphToVercelAdapter

# Extract from custom field
extractor = structured_data_extractor("summary")
adapter = LangGraphToVercelAdapter(message_extractor=extractor)
```

---

## Testing

### V1 Testing
```python
# Hard to test - tightly coupled to graph
# Need to mock entire graph execution
```

### V2 Testing
```python
# Easy to test - separated components
def test_adapter():
    adapter = LangGraphToVercelAdapter()

    # Mock simple graph
    simple_graph = create_test_graph()

    # Test streaming
    events = adapter.stream(simple_graph, state, config)
    assert events  # Easy to verify!
```

See `tests/test_langgraph_vercel_adapter.py` for complete examples.

---

## Recommendations

### Use `/chat/v2` if:
- ✅ You're starting a new project
- ✅ You value clean architecture
- ✅ You might customize message extraction
- ✅ You plan to reuse streaming with other graphs
- ✅ You want easier testing and maintenance

### Use `/chat` if:
- ✅ You have existing integrations
- ✅ You need maximum stability
- ✅ You don't plan to customize
- ✅ "If it ain't broke, don't fix it"

### Use `/chat-sync` if:
- ⚠️ You're maintaining legacy code
- ⚠️ Your client doesn't support SSE
- ❌ Don't use for new projects

---

## Future Plans

- **Short term:** Monitor `/chat/v2` performance and stability
- **Medium term:** Migrate existing integrations from `/chat` to `/chat/v2`
- **Long term:** Deprecate `/chat` in favor of `/chat/v2`
- **Legacy:** Keep `/chat-sync` for backward compatibility only

---

## Summary

**TL;DR:**
- **New projects:** Use `/chat/v2` ← Recommended
- **Existing projects:** Keep using `/chat` (or migrate to v2)
- **Legacy support:** `/chat-sync` is available but discouraged

Both streaming endpoints (`/chat` and `/chat/v2`) provide identical functionality to the user. The difference is in **code quality, maintainability, and reusability**.

Choose `/chat/v2` for a better developer experience and cleaner architecture.
