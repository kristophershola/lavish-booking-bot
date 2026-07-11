# Cinema business rules. Internal hall names are never exposed to customers,
# the booking engine assigns a hall automatically.

from config import HALL_TABS  # actual sheet tab names, e.g. "HALL 1", "HALL 2"

INTERNAL_HALLS = ["Hall 1", "Hall 2"]  # display labels only, never expose to customers

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
    """Checks both halls for the given date and session, returns whichever
    hall tab name is free, or None if both are occupied. The hall name is
    for internal use only, it must never be shown to a customer.
    """
    from services.sheets import get_hall_tab_rows, is_session_available

    for hall_tab in HALL_TABS:
        rows = get_hall_tab_rows(hall_tab)
        available = is_session_available(rows, date, session_index)
        if available:
            return hall_tab
    return None


def check_double_session_availability(date, first_session_index):
    """For XTRA TIME bookings, verifies both the requested session and the
    immediately following session are free in the same hall. Returns the
    available hall tab name, or None if no single hall has both slots free.
    """
    from services.sheets import get_hall_tab_rows, is_session_available

    if first_session_index >= len(SESSIONS) - 1:
        return None  # no following session exists to pair with

    for hall_tab in HALL_TABS:
        rows = get_hall_tab_rows(hall_tab)
        first_available = is_session_available(rows, date, first_session_index)
        second_available = is_session_available(rows, date, first_session_index + 1)
        if first_available and second_available:
            return hall_tab
    return None
