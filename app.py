from fastapi import FastAPI

from routes.webhook import router as webhook_router
from services.instagram import fetch_recent_conversation_messages
from state.conversation import seed_processed_ids

app = FastAPI()
app.include_router(webhook_router)


@app.on_event("startup")
async def seed_processed_messages_on_startup():
    recent_messages = fetch_recent_conversation_messages(limit=10)
    seed_processed_ids([m.get("id") for m in recent_messages])
