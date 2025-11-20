from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.api.models.travel_system import (
    TravelSystemChatRequest,
    TravelSystemChatResponse,
    VercelChatRequest,
)
from app.api.services.travel_system_service import process_travel_system_chat
from app.api.services.travel_system_streaming_service import stream_travel_system_chat
from app.utils.vercel_stream import patch_vercel_headers
from app.utils.message_transformer import extract_user_message

router = APIRouter()


@router.post("/chat")
async def travel_system_chat_streaming(request: VercelChatRequest):
    """
    Streaming chat endpoint for the full travel system pipeline.
    Handles requirements gathering, itinerary planning, and bookings.

    Accepts Vercel AI SDK request format and transforms UI messages internally.
    Uses Vercel Data Stream Protocol for real-time streaming to frontend.
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


@router.post("/chat-sync", response_model=TravelSystemChatResponse)
async def travel_system_chat_sync(request: TravelSystemChatRequest):
    """
    Legacy synchronous chat endpoint for the full travel system pipeline.

    This endpoint is kept for backward compatibility.
    New clients should use the streaming /chat endpoint.
    """
    message, is_interrupt, requirements, itinerary, bookings = process_travel_system_chat(
        request.message, request.thread_id, request.resume
    )

    return TravelSystemChatResponse(
        message=message,
        is_interrupt=is_interrupt,
        requirements=requirements,
        itinerary=itinerary,
        bookings=bookings,
    )

