# Lavish Booking AI, Software Requirements Specification

This file is a placeholder. The actual source of truth is the **Lavish Booking AI Specification** document established during Phase 1 (Business Rules) and Phase 2 (Conversation Design), before any code was written.

If that document lives elsewhere (Google Docs, Notion, etc.), consider copying its current contents into this file so the specification travels with the codebase and stays version controlled alongside the code it governs.

## Current project phase

- Phase 1, Business Rules: complete
- Phase 2, Conversation Design: in progress
- Phase 3, Booking Engine: not started (see `booking/` module stubs)
- Phase 4, AI Agent: in progress (Gemini wired in via `ai/gemini.py`, OpenAI swap still to come)
- Phase 5, Instagram Integration: working end to end for text messages, webhook verified, replies sending successfully

## Known open items

- Finalise the bot's opening message for new conversations
- Compile an approved FAQ list
- Persist `state/conversation.py`'s in memory history and processed message ids somewhere durable, so a Railway restart mid conversation cannot lose context or replay old messages
- Add AI based preliminary checks on payment receipt images before staff approval (prototyped previously during the Botpress phase)
