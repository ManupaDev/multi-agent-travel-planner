from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.agents.response_models.requirements_agent import CompleteRequirements


class RequirementsChatRequest(BaseModel):
    """Legacy request format - kept for backward compatibility"""
    message: str
    thread_id: str
    resume: bool = False


class VercelChatRequest(BaseModel):
    """
    Vercel AI SDK request format.
    Accepts the standard UI messages format and transforms internally.
    """
    id: str  # Conversation ID from frontend
    messages: List[Dict[str, Any]]  # UI messages array
    trigger: str  # "submit-message" or other triggers
    thread_id: Optional[str] = None  # Optional override for thread_id
    resume: Optional[bool] = False  # Whether resuming from interrupt


class RequirementsChatResponse(BaseModel):
    message: str
    is_interrupt: bool
    requirements: Optional[CompleteRequirements] = None
