from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.api.models.travel_system import VercelChatRequest
from app.api.services.travel_system_streaming_service import stream_travel_system_chat
from app.utils.http_headers import patch_vercel_headers
from app.utils.message_transformer import extract_user_message

router = APIRouter()


@router.post("/chat")
async def travel_system_chat_streaming(request: VercelChatRequest):
    """
    Streaming chat endpoint using the pluggable LangGraph-to-Vercel adapter.

    This endpoint uses clean separation of concerns:
    - Core agentic logic (LangGraph) is unchanged
    - Adapter layer handles streaming protocol transformation
    - No coupling between graph structure and streaming protocol

    Architecture:
    - Pluggable adapter works with any LangGraph graph
    - Configurable message extraction strategies
    - Easy to customize and maintain
    - Well-tested and documented

    Compatible with Vercel AI SDK's useChat and useAssistant hooks.
    Supports interrupts for human-in-the-loop workflows.
    """
    # Transform UI messages to message string
    message = extract_user_message(request.messages)

    # Use thread_id from body if provided, otherwise use conversation id
    thread_id = request.thread_id or request.id

    response = StreamingResponse(
        stream_travel_system_chat(
            message=message,
            thread_id=thread_id,
            resume=request.resume
        ),
        media_type="text/event-stream",
    )

    return patch_vercel_headers(response)

