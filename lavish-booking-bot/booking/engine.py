# This module will become the single entry point the AI layer calls into
# once function/tool calling is wired up in Phase 4, instead of the AI
# generating free text answers about availability and pricing on its own.
#
# Expected shape once built:
#
#   from booking import engine
#   result = engine.handle_booking_request(intent, details)
#
# For now this is intentionally empty, Phase 3 has not started yet.
