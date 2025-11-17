from pydantic import BaseModel, Field
from typing import Optional, List

# Core content schemas
class Book(BaseModel):
    title: str
    year: int
    description: str
    slug: str
    palette: List[str] = Field(default_factory=list)


class TVWork(BaseModel):
    title: str
    role: str


# Chat persistence schema
class ChatMessage(BaseModel):
    username: str
    content: str
    season: str
    depth: float = 0.0
    thread_id: Optional[str] = None
