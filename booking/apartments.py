# Apartment business rules. Internal unit names are never exposed to customers.
#
# Internal units: A1, B1, B2, C1, C2 (5 total)
# A 2 Bedroom booking blocks the entire unit regardless of headcount.

APARTMENT_TIERS = {
    "2_bedroom": {"label": "2 Bedroom", "price_per_night": 80000},
    "3_bedroom": {"label": "3 Bedroom", "price_per_night": 90000},
}

SPECIAL_EVENT_RATE = {
    "label": "Special Event / Party",
    "price_per_night": 200000,
    "trigger_headcount": 10,  # triggered when MORE than this many people will be present
}

INTERNAL_UNITS = ["A1", "B1", "B2", "C1", "C2"]  # never expose to customers


def check_apartment_availability(date, tier):
    """Phase 3 work. Will read the Google Sheet (read-only) and return
    whether a unit matching the requested tier is free on the given date.
    """
    raise NotImplementedError("Booking engine not yet built, see Phase 3 in project plan.")


def calculate_apartment_price(tier, headcount, nights=1):
    """Phase 3 work. Applies the Special Event override when headcount
    exceeds SPECIAL_EVENT_RATE['trigger_headcount'], otherwise uses the
    requested tier's standard nightly rate.
    """
    raise NotImplementedError("Booking engine not yet built, see Phase 3 in project plan.")
