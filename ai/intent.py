# Not yet wired into the live flow.
#
# This is where future intent classification will live, once the booking
# engine (Phase 3) exists and the bot needs to decide things like:
#   - is this an apartment enquiry or a cinema enquiry
#   - has the customer provided enough detail to check availability
#   - has the customer indicated they are ready to pay
#
# For now, all messages go straight to Gemini as free text via ai/gemini.py,
# and Gemini handles this reasoning itself through the system prompt.
# Once booking/engine.py exists, this module will likely detect structured
# intents and call specific booking functions instead of relying purely on
# free form generation.


def detect_intent(message_text):
    raise NotImplementedError("Intent detection is not implemented yet, this is a Phase 4/5 placeholder.")
