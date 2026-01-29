from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

class Conversation(BaseModel):
    id: str
    title: str
    source: str
    messages: List[Message]
    createdAt: str
    updatedAt: str
    selected: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
