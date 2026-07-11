from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os

from routes.webhook import router as webhook_router
from routes.debug import router as debug_router
from services.instagram import fetch_recent_conversation_messages
from state.conversation import seed_processed_ids

app = FastAPI()
app.include_router(webhook_router)
app.include_router(debug_router)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
async def seed_processed_messages_on_startup():
    recent_messages = fetch_recent_conversation_messages(limit=10)
    seed_processed_ids([m.get("id") for m in recent_messages])
