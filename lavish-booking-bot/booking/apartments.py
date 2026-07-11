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


def check_apartment_availability(date):
    """Returns True if at least one apartment unit is free on the given
    date, regardless of which tier the customer wants, since all 5 units
    support all tiers. Scans every unit tab before concluding
    unavailability, never stops at the first booked one.
    """
    from services.sheets import check_any_apartment_available
    is_available, _available_units = check_any_apartment_available(date)
    return is_available


def calculate_apartment_price(tier, headcount=None, nights=1):
    """Applies the Special Event override when headcount exceeds the
    trigger threshold, otherwise uses the requested tier's standard
    nightly rate.
    """
    if headcount is not None and headcount > SPECIAL_EVENT_RATE["trigger_headcount"]:
        nightly_rate = SPECIAL_EVENT_RATE["price_per_night"]
    else:
        nightly_rate = APARTMENT_TIERS[tier]["price_per_night"]
    return nightly_rate * nights
