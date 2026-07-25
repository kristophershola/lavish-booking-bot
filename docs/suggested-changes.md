# Suggested Changes

Notes from a project review on 2026-07-25. Nothing here has been applied yet, this is a punch list to work through.

## 1. Docs are stale

`docs/SRS.md` says "Phase 3, Booking Engine, not started" but `booking/apartments.py` and `booking/cinema.py` are fully wired and working against live Sheets data. Meanwhile `booking/availability.py`, `booking/pricing.py`, and `booking/engine.py` are dead stub files describing a design that was superseded. Either delete these three files or clearly mark them as obsolete so the codebase does not confuse the next person.

## 2. Debug route has no auth

`routes/debug.py` exposes `/debug/sheets?tab=...` with no authentication. It can dump full sheet contents, including guest names, to anyone who finds the URL. Fine for local testing, risky if deployed as is. Add an auth check or remove the route before going to production.

## 3. Menu image URL is hardcoded

`ai/tools.py`'s `send_menu_image` hardcodes a GitHub raw URL with a specific username baked in, even though `config.py` already defines `APP_URL` for this exact purpose. Use `APP_URL` and serve the image from the app's own `/static` mount instead of GitHub.

## 4. Conversation state is not durable

`state/conversation.py` and `state/user_state.py` keep conversation history, user state, and processed message ids only in memory. A Railway restart mid conversation loses all context and can replay old messages. This is already flagged as a known gap in `docs/SRS.md`. Move this to the Google Sheet or a small database before going live.

## 5. History window is tight

`MAX_HISTORY_TURNS = 2` in `config.py` is tight for a multi step booking flow (date, tier, session, package, payment). Understandable given Groq free tier limits, but worth revisiting once request volume allows a higher limit or a paid tier.

## 6. Deprecated FastAPI startup pattern

`app.py` uses `@app.on_event("startup")`, which is deprecated upstream. Switch to a `lifespan` context manager.

## 7. Unpinned dependencies

`requirements.txt` has no pinned versions. Pin versions for reproducible deploys, especially before production use.
