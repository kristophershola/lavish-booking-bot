# Cinema business rules. Internal hall names are never exposed to customers,
# the booking engine assigns a hall automatically.

INTERNAL_HALLS = ["Hall 1", "Hall 2"]  # never expose to customers

SESSIONS = [
    {"label": "9:30 to 11:50am", "start": "09:30", "end": "11:50"},
    {"label": "12:00 to 2:20pm", "start": "12:00", "end": "14:20"},
    {"label": "2:30 to 4:50pm", "start": "14:30", "end": "16:50"},
    {"label": "5:00 to 7:20pm", "start": "17:00", "end": "19:20"},
    {"label": "7:30 to 9:50pm", "start": "19:30", "end": "21:50"},
    {"label": "10:00pm to midnight", "start": "22:00", "end": "00:00"},
]

PACKAGES = {
    "crunch_and_drink": {"label": "Crunch and Drink", "price": 25000},
    "byof": {"label": "BYOF", "price": 25000},
    "crunch_and_wine": {"label": "Crunch and Wine", "price": 30000},
    "slice_and_drink": {"label": "Slice and Drink", "price": 40000},
    "slice_and_wine": {"label": "Slice and Wine", "price": 45000},
    "executive": {"label": "Executive", "price": 55000},
}


def find_available_hall(date, session_index):
    """Phase 3 work. Reads the HALL 1 / HALL 2 tabs and returns whichever
    hall is free for the requested date and session, without ever
    revealing the hall name to the customer.
    """
    raise NotImplementedError("Booking engine not yet built, see Phase 3 in project plan.")


def check_double_session_availability(date, first_session_index):
    """Phase 3 work. For XTRA TIME bookings, verifies both the requested
    session and the immediately following session are free on the same hall.
    """
    raise NotImplementedError("Booking engine not yet built, see Phase 3 in project plan.")
