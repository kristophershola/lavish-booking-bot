# Not yet used.
#
# Once the booking engine (Phase 3) exists, this is where structured
# per-conversation state will likely live, for example tracking which
# booking stage a customer is in (see booking/payments.py BOOKING_STAGES),
# which service they are enquiring about, and which details have already
# been collected. Right now the bot relies purely on the raw Gemini
# conversation history in state/conversation.py, with no structured
# tracking on top of it.
