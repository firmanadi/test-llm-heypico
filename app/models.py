from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    user_location: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    places: Optional[List[Dict[str, Any]]] = None
    map_data: Optional[Dict[str, Any]] = None

class PlaceSearchRequest(BaseModel):
    query: str
    location: Optional[str] = None
    radius: int = 5000
    place_type: Optional[str] = None

class DirectionsRequest(BaseModel):
    origin: str
    destination: str
    mode: str = "driving"
    alternatives: bool = True
