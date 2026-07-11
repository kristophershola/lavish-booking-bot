from datetime import datetime

from booking.apartments import check_apartment_availability, calculate_apartment_price
from booking.cinema import find_available_hall, check_double_session_availability, list_available_cinema_sessions

# Groq (OpenAI-compatible) function calling tool declarations. Descriptions
# are written for the model, so it knows exactly when and how to call each one.
TOOL_DECLARATIONS = [
    {
        "type": "function",
        "function": {
            "name": "check_apartment_availability",
            "description": (
                "Checks whether at least one apartment unit is free on a given date. "
                "Use this whenever a customer asks about apartment availability for a "
                "specific date, regardless of which tier (2 Bedroom, 3 Bedroom, or "
                "Special Event) they eventually choose, since all units support all tiers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_apartment_price",
            "description": (
                "Calculates the nightly price for an apartment booking. Automatically "
                "applies the Special Event rate if headcount exceeds 10 people."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "enum": ["2_bedroom", "3_bedroom"],
                        "description": "The apartment tier the customer wants, ignored if headcount triggers the Special Event rate instead."
                    },
                    "headcount": {
                        "type": "integer",
                        "description": "Total number of people expected, including visitors. Omit if not mentioned."
                    },
                    "nights": {
                        "type": "integer",
                        "description": "Number of nights, defaults to 1 if not specified."
                    }
                },
                "required": ["tier"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_cinema_sessions",
            "description": (
                "Checks all 6 cinema sessions for a given date and returns a list of "
                "available session indices (0-5). Use this when a customer asks about "
                "cinema availability for a date, before asking which session they prefer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                    }
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_available_hall",
            "description": (
                "Checks whether a specific cinema session is available on a given date. "
                "Use this after the customer has chosen a session from the available "
                "options returned by list_available_cinema_sessions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                    },
                    "session_index": {
                        "type": "integer",
                        "description": "0 for 9:30-11:50am, 1 for 12:00-2:20pm, 2 for 2:30-4:50pm, 3 for 5:00-7:20pm, 4 for 7:30-9:50pm, 5 for 10:00pm-midnight."
                    }
                },
                "required": ["date", "session_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_double_session_availability",
            "description": (
                "Checks whether two consecutive cinema sessions are both free on a given "
                "date, for an XTRA TIME double session booking. Use this only when a "
                "customer explicitly wants a double length session spanning two sessions "
                "(also called 'Extra Time' or 'XTRA TIME')."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "The exact calendar date to check, in YYYY-MM-DD format."
                    },
                    "first_session_index": {
                        "type": "integer",
                        "description": "Index (0 through 4) of the first of the two consecutive sessions."
                    }
                },
                "required": ["date", "first_session_index"]
            }
        }
    }
]


# Gemini uses a different schema shape (function_declarations wrapped in
# one dict, uppercase JSON types) but the same underlying tools and
# descriptions as the Groq declarations above. Kept in sync manually since
# there are only five tools.
GEMINI_TOOL_DECLARATIONS = [
    {
        "function_declarations": [
            {
                "name": "check_apartment_availability",
                "description": (
                    "Checks whether at least one apartment unit is free on a given date. "
                    "Use this whenever a customer asks about apartment availability for a "
                    "specific date, regardless of which tier (2 Bedroom, 3 Bedroom, or "
                    "Special Event) they eventually choose, since all units support all tiers."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "calculate_apartment_price",
                "description": (
                    "Calculates the nightly price for an apartment booking. Automatically "
                    "applies the Special Event rate if headcount exceeds 10 people."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "tier": {
                            "type": "STRING",
                            "enum": ["2_bedroom", "3_bedroom"],
                            "description": "The apartment tier the customer wants, ignored if headcount triggers the Special Event rate instead."
                        },
                        "headcount": {
                            "type": "INTEGER",
                            "description": "Total number of people expected, including visitors. Omit if not mentioned."
                        },
                        "nights": {
                            "type": "INTEGER",
                            "description": "Number of nights, defaults to 1 if not specified."
                        }
                    },
                    "required": ["tier"]
                }
            },
            {
                "name": "list_available_cinema_sessions",
                "description": (
                    "Checks all 6 cinema sessions for a given date and returns a list of "
                    "available session indices (0-5). Use this when a customer asks about "
                    "cinema availability for a date, before asking which session they prefer."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "find_available_hall",
                "description": (
                    "Checks whether a specific cinema session is available on a given date. "
                    "Use this after the customer has chosen a session from the available "
                    "options returned by list_available_cinema_sessions."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "The exact calendar date to check, in YYYY-MM-DD format, resolved using the DATE CONTEXT provided."
                        },
                        "session_index": {
                            "type": "INTEGER",
                            "description": "0 for 9:30-11:50am, 1 for 12:00-2:20pm, 2 for 2:30-4:50pm, 3 for 5:00-7:20pm, 4 for 7:30-9:50pm, 5 for 10:00pm-midnight."
                        }
                    },
                    "required": ["date", "session_index"]
                }
            },
            {
                "name": "check_double_session_availability",
                "description": (
                    "Checks whether two consecutive cinema sessions are both free on a given "
                    "date, for an XTRA TIME double session booking. Use this only when a "
                    "customer explicitly wants a double length session spanning two sessions "
                    "(also called 'Extra Time' or 'XTRA TIME')."
                ),
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "The exact calendar date to check, in YYYY-MM-DD format."
                        },
                        "first_session_index": {
                            "type": "INTEGER",
                            "description": "Index (0 through 4) of the first of the two consecutive sessions."
                        }
                    },
                    "required": ["date", "first_session_index"]
                }
            }
        ]
    }
]


def _parse_iso_date(date_string):
    return datetime.strptime(date_string, "%Y-%m-%d").date()


def _coerce_int(value, default=None):
    """Models occasionally pass numbers as strings, e.g. "3" instead of 3.
    This coerces safely rather than letting arithmetic fail downstream.
    """
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def execute_tool(name, args):
    """Dispatches a tool call to the real booking logic and returns a plain
    dict suitable for sending back as a tool result. Never lets internal
    unit or hall names leak into the response, only availability booleans.
    """
    try:
        if name == "check_apartment_availability":
            date = _parse_iso_date(args["date"])
            available = check_apartment_availability(date)
            return {"available": available}

        if name == "calculate_apartment_price":
            tier = args["tier"]
            headcount = _coerce_int(args.get("headcount"))
            nights = _coerce_int(args.get("nights"), default=1)
            price = calculate_apartment_price(tier, headcount=headcount, nights=nights)
            return {"total_price_naira": price, "nights": nights}

        if name == "list_available_cinema_sessions":
            date = _parse_iso_date(args["date"])
            from booking.cinema import list_available_cinema_sessions
            available_indices = list_available_cinema_sessions(date)
            return {"available_sessions": available_indices}

        if name == "find_available_hall":
            date = _parse_iso_date(args["date"])
            session_index = _coerce_int(args["session_index"])
            hall = find_available_hall(date, session_index)
            return {"available": hall is not None}

        if name == "check_double_session_availability":
            date = _parse_iso_date(args["date"])
            first_session_index = _coerce_int(args["first_session_index"])
            hall = check_double_session_availability(date, first_session_index)
            return {"available": hall is not None}

        return {"error": f"Unknown tool: {name}", "error_type": "unknown_tool"}

    except ValueError as exc:
        # Date format errors
        print(f"TOOL DATE FORMAT ERROR for {name} with args {args}: {exc}")
        return {"error": "Invalid date format. Use YYYY-MM-DD.", "error_type": "date_format"}
    except Exception as exc:
        print(f"TOOL EXECUTION ERROR for {name} with args {args}: {exc}")
        return {"error": "Something went wrong checking that, please try again in a moment.", "error_type": "execution"}
