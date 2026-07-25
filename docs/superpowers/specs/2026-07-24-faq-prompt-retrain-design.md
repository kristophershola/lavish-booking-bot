# FAQ Accuracy & Conversation Flow Tuning — Design Spec

## Goal

Use the WhatsApp/Meta AI export data (~150 FAQ entries + 404 conversations) to improve the existing `lavish-booking-bot` by:
1. Updating the system prompt to match Lavish Living's approved FAQ answers exactly
2. Tuning conversation flows based on real customer interaction patterns

## Approach Selected

**Approach 1: System Prompt Refresh** — Rewrite `ai/prompts.py` with data extracted from `settings.txt` and conversation-pattern analysis. No new dependencies, no infrastructure changes.

## Data Sources

- `C:\Users\PC\Downloads\file enc\settings.txt` — Meta AI configuration with ~150 FAQ entries, business info, packages, pricing, policies
- `C:\Users\PC\Downloads\file enc\conversations\*.txt` — 404 real customer conversations showing bot responses, human handoffs, and successful booking flows

## Section 1: Data Extraction Plan

1.1 Parse `settings.txt` into a structured JSON file (`data/faqs.json`) with categories:
  - `business_info` — address, hours, website, payment accounts
  - `apartment_faqs` — pricing, tiers, check-in/out, special events, discounts, policies
  - `cinema_faqs` — packages, prices, session times, capacity, hall rules
  - `house_rules` — smoking, quiet hours, guests, pets, damages, waste disposal
  - `policies` — refunds, rescheduling, deposits, booking lead times

1.2 Analyze conversations to catalog handoff points:
  - Search all conversations for "Unfortunately I can't help you with that" / "Let me connect you" patterns
  - Identify the triggering customer question for each
  - Prioritize gaps for patching based on frequency

1.3 Catalog successful flows:
  - Map complete apartment booking flows (greeting → info → date → quiet/party → tier → availability → price → payment)
  - Map complete cinema booking flows (greeting → date → sessions → package → payment)

## Section 2: System Prompt Rewrite Plan

2.1 Restructure `SYSTEM_PROMPT` in `ai/prompts.py` into clear blocks:

  **Block A — Business Info**
  - Full address: "5 M.M Alkali Street, Citec Villa, 4th Avenue, Gwarimpa"
  - Hours: 24/7
  - Website: https://lavishliving.ng
  - Google Maps: "Lavish Apartment"

  **Block B — Payment Details** (mostly exists, refine wording)
  - Zenith: 1219550382 (Lavish Living LTD)
  - Moniepoint: 6397001960 (Lavish Apartments)
  - Deposit policy: 50% non-refundable deposit accepted for apartments
  - Cinema: full payment required, no deposits
  - Receipt verification: screenshot showing both sender/receiver names

  **Block C — Key FAQs** (top 15-20 most-asked from data)
  - Monthly rate: ₦2.1m
  - Discount: 4+ nights
  - Capacity: cinema 6 max, apartment 10 max
  - Special event: >10 guests = ₦200k/night
  - Check-in: 2pm / Check-out: 12pm
  - Reschedule: ₦15k fee, within 1 week
  - Refunds: not offered, 3-5 business days if applicable
  - Movie selection: from website list
  - BYOF/Executive: outside food allowed
  - Location distance: 20 min from stadium, 10-15 min from Efab

  **Block D — House Rules** (currently absent, add from settings.txt)
  - No smoking inside
  - Quiet hours 11pm-8am
  - No pets
  - No sex in cinema halls
  - No video recording of screenings
  - Report damages immediately

  **Block E — Booking Flows** (refine existing)

2.2 Validate every factual statement in the prompt against `settings.txt` — remove any contradictions.

## Section 3: Conversation Flow Tuning Plan

3.1 **Add monthly/long-stay handling**
  - If customer asks about monthly/long stay: quote ₦2.1m for monthly
  - Prompt already handles 4+ night discounts

3.2 **Combine apartment + cinema queries**
  - If customer asks about both in same conversation (common for birthdays), handle sequentially without starting over

3.3 **Handle walk-in / check-in queries**
  - "I'm nearby" / "Can I come now": provide address and hours, ask if they have a booking

3.4 **Handle specific unit references**
  - If customer mentions B2, A1, etc. (from website): acknowledge but redirect to assigned-by-availability

3.5 **Capacity precision**
  - Hall 1: max 4 people, Hall 2: max 6 people (currently vague)

## Files Modified

- `ai/prompts.py` — system prompt rewrite (primary)
- `data/faqs.json` — new structured FAQ file (created during extraction, for reference)

## Out of Scope

- No new dependencies (no vector DB, no fine-tuning)
- No WhatsApp channel addition (just using the data to improve the Instagram bot)
- No changes to booking engine logic (`booking/*.py`)
- No changes to webhook routing (`routes/webhook.py`)
- No changes to conversation state management

## Success Criteria

1. Bot can answer all ~150 FAQ scenarios with the exact approved answers from settings.txt
2. Reduced frequency of "Unfortunately I can't help you with that" handoffs (measure against baseline)
3. Monthly rate queries produce correct ₦2.1m answer instead of handoff
4. Cinema capacity answers are precise (Hall 1: 4, Hall 2: 6)
