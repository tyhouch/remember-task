from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import asyncio
from sqlalchemy.orm import Session

from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.models.memory import get_db

load_dotenv()

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

def get_llm_service():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    return LLMService(api_key)

def get_memory_service(db: Session = Depends(get_db)):
    return MemoryService(db)

@router.post("")
async def chat_post(
    request: ChatRequest, 
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Process a chat message via POST and return a streaming response
    """
    return StreamingResponse(
        llm_service.stream_response(request.message, memory_service),
        media_type="text/event-stream"
    )

@router.get("")
async def chat_get(
    request: Request, 
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Process a chat message via GET and return a streaming response
    """
    message = request.query_params.get("message", "")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    return StreamingResponse(
        llm_service.stream_response(message, memory_service),
        media_type="text/event-stream"
    ) 