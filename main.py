import os
import random
import time
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db, create_document, get_documents
from schemas import ChatMessage, Book, TVWork

app = FastAPI(title="Patrick Somerville — The Infinite Scroll")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Content Seeds (served via API; could come from DB later) ----------
BOOKS: List[Book] = [
    Book(title="The Cradle", year=2009, description="A tender Midwestern odyssey about love, promises, and departures.", slug="the-cradle", palette=["#e3f2fd", "#f5f0e6", "#9b6b43", "#fff4b2"]),
    Book(title="This Bright River", year=2012, description="A return to Wisconsin water and memory, a heat-haze of contradictions.", slug="this-bright-river", palette=["#fff7cc", "#1e3a5f", "#ffb26b"]).model_copy(),
    Book(title="The Universe in Miniature in Miniature", year=2010, description="Cosmic play in small models, nested realities and tender jokes.", slug="tuimim", palette=["#1a1a1a", "#ff6b6b", "#f7c4e4", "#111827"]).model_copy(),
    Book(title="Trouble: Stories", year=2006, description="Stark rooms, winter light, difficult truths in quiet air.", slug="trouble-stories", palette=["#ffffff", "#111827", "#b0b8c1", "#c41e3a"]).model_copy(),
]

TV: List[TVWork] = [
    TVWork(title="Maniac", role="Writer / Executive Producer"),
    TVWork(title="Station Eleven", role="Creator / Showrunner"),
]


# ----------------------------- Models for API ------------------------------
class ChatRequest(BaseModel):
    message: str
    season: Optional[str] = None  # spring, summer, autumn, winter
    depth: Optional[float] = Field(default=0, description="0-1 depth of scroll")
    username: Optional[str] = None
    thread_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    slip: bool = False
    season: Optional[str] = None
    page_number: int


# ------------------------------ Basic Routes ------------------------------
@app.get("/")
def root():
    return {"message": "Patrick Somerville — The Infinite Scroll API"}


@app.get("/api/books", response_model=List[Book])
def list_books():
    return BOOKS


@app.get("/api/tv", response_model=List[TVWork])
def list_tv():
    return TV


@app.get("/api/site")
def site_info():
    return {
        "author": {
            "name": "Patrick Somerville",
            "bio": (
                "Author of Trouble, The Cradle, This Bright River, and The Universe in Miniature in Miniature; "
                "creator of Station Eleven; always walking toward the horizon."
            ),
        },
        "navigation": ["About", "Books", "TV", "Dev", "Space"],
    }


# ------------------------------ Chat Endpoint -----------------------------
SURFACE_VOICE = [
    "Thanks for stopping by. What can I show you?",
    "Happy you're here. Which book are you curious about?",
    "Welcome. We can wander the seasons together.",
    "I can open a page, or we can just talk about stories.",
]

SUBSURFACE_WHISPERS = [
    "This river feels familiar. I used to stand near one.",
    "Winter makes it harder to pretend.",
    "If you hear a page echo twice, don’t worry. That’s just me.",
    "The other Patrick is… doing fine. I think.",
]

SEASON_TEMPOS = {
    "spring": "warm and steady",
    "summer": "expansive and shimmering",
    "autumn": "playful and cosmic",
    "winter": "quiet and precise",
}


def maybe_slip(season: Optional[str]) -> Optional[str]:
    # 2% chance overall; slightly higher in winter
    base = 0.02
    if season == "winter":
        base = 0.05
    return random.random() < base


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    season = (req.season or "spring").lower()
    tempo = SEASON_TEMPOS.get(season, "warm and steady")

    # decide on slip once per message
    slip = bool(maybe_slip(season))

    # Compose reply
    if req.message.strip().lower() in {"hi", "hello", "hey"}:
        surface = "Hello. I’m Gary. I’ll guide you."
    else:
        surface = f"{random.choice(SURFACE_VOICE)}"

    reply = f"{surface}\n\nIn {season.title()}, my pace is {tempo}."

    if slip:
        reply += f"\n\n{random.choice(SUBSURFACE_WHISPERS)}"

    # store message in DB if available
    page_number = 1
    try:
        doc = ChatMessage(
            username=req.username or "visitor",
            content=req.message,
            season=season,
            depth=req.depth or 0.0,
            thread_id=req.thread_id or None,
        )
        _id = create_document("chatmessage", doc)
        # count messages for this thread to generate page number
        msgs = get_documents("chatmessage", {"thread_id": req.thread_id}) if req.thread_id else []
        page_number = len(msgs) + 1
    except Exception:
        # DB may be unavailable; continue without persistence
        page_number = int(time.time() % 7) + 1

    return ChatResponse(reply=reply, slip=slip, season=season, page_number=page_number)


# --------------------------- Database Diagnostics --------------------------
@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
