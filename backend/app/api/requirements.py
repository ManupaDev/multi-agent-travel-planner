from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.api.models.requirements import (
    RequirementsChatRequest,
    RequirementsChatResponse,
    VercelChatRequest,
)
from app.api.services.requirements_service import process_requirements_chat
from app.api.services.requirements_streaming_service import stream_requirements_chat
from app.utils.vercel_stream import patch_vercel_headers
from app.utils.message_transformer import extract_user_message

router = APIRouter()


@router.post("/chat")
async def requirements_chat_streaming(request: VercelChatRequest):
    """
    Streaming chat endpoint for requirements gathering.

    Accepts Vercel AI SDK request format and transforms UI messages internally.
    Uses Vercel Data Stream Protocol for real-time streaming to frontend.
    Supports interrupts when additional information is needed.
    """
    # Transform UI messages to message string
    message = extract_user_message(request.messages)

    # Use thread_id from body if provided, otherwise use conversation id
    thread_id = request.thread_id or request.id

    response = StreamingResponse(
        stream_requirements_chat(
            message=message,
            thread_id=thread_id,
            resume=request.resume
        ),
        media_type="text/event-stream",
    )

    return patch_vercel_headers(response)


@router.post("/chat-sync", response_model=RequirementsChatResponse)
async def requirements_chat_sync(request: RequirementsChatRequest):
    """
    Legacy synchronous chat endpoint for requirements gathering.

    This endpoint is kept for backward compatibility.
    New clients should use the streaming /chat endpoint.
    """
    message, is_interrupt, requirements = process_requirements_chat(
        request.message, request.thread_id, request.resume
    )

    return RequirementsChatResponse(
        message=message, is_interrupt=is_interrupt, requirements=requirements
    )
