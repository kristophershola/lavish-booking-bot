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
            "description": "Check if any apartment is free on a given date (YYYY-MM-DD). Call when customer asks about apartment availability for a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format from DATE CONTEXT."
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
            "description": "Calculate nightly price for an apartment booking. Use Special Event rate if headcount > 10.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tier": {
                        "type": "string",
                        "enum": ["2_bedroom", "3_bedroom"],
                        "description": "Apartment tier (ignored if Special Event rate applies)."
                    },
                    "headcount": {
                        "type": "integer",
                        "description": "Total people expected. Omit if not mentioned."
                    },
                    "nights": {
                        "type": "integer",
                        "description": "Number of nights. Default 1."
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
            "description": "Check all 6 cinema sessions for a date, returns available indices (0-5). Call before asking which session they prefer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format from DATE CONTEXT."
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
            "description": "Confirm a specific cinema session is still free. Call after customer picks a session.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format."
                    },
                    "session_index": {
                        "type": "integer",
                        "description": "0=9:30-11:50am, 1=12:00-2:20pm, 2=2:30-4:50pm, 3=5:00-7:20pm, 4=7:30-9:50pm, 5=10:00pm-midnight."
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
            "description": "Check if two consecutive cinema sessions are free (XTRA TIME / Extra Time). Only call when customer explicitly asks for double/Extra Time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format."
                    },
                    "first_session_index": {
                        "type": "integer",
                        "description": "Index (0-4) of the first of two consecutive sessions."
                    }
                },
                "required": ["date", "first_session_index"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_menu_image",
            "description": "Send cinema menu image to customer. Only call when customer explicitly asks about menu/packages/prices/how much. NEVER call when customer mentions a date or session.",
            "parameters": {
                "type": "object",
                "properties": {}
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
                "description": "Check if any apartment is free on a given date (YYYY-MM-DD). Call when customer asks about apartment availability for a specific date.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "Date in YYYY-MM-DD format from DATE CONTEXT."
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "calculate_apartment_price",
                "description": "Calculate nightly price for an apartment booking. Use Special Event rate if headcount > 10.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "tier": {
                            "type": "STRING",
                            "enum": ["2_bedroom", "3_bedroom"],
                            "description": "Apartment tier (ignored if Special Event rate applies)."
                        },
                        "headcount": {
                            "type": "INTEGER",
                            "description": "Total people expected. Omit if not mentioned."
                        },
                        "nights": {
                            "type": "INTEGER",
                            "description": "Number of nights. Default 1."
                        }
                    },
                    "required": ["tier"]
                }
            },
            {
                "name": "list_available_cinema_sessions",
                "description": "Check all 6 cinema sessions for a date, returns available indices (0-5). Call before asking which session they prefer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "Date in YYYY-MM-DD format from DATE CONTEXT."
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "find_available_hall",
                "description": "Confirm a specific cinema session is still free. Call after customer picks a session.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "Date in YYYY-MM-DD format."
                        },
                        "session_index": {
                            "type": "INTEGER",
                            "description": "0=9:30-11:50am, 1=12:00-2:20pm, 2=2:30-4:50pm, 3=5:00-7:20pm, 4=7:30-9:50pm, 5=10:00pm-midnight."
                        }
                    },
                    "required": ["date", "session_index"]
                }
            },
            {
                "name": "check_double_session_availability",
                "description": "Check if two consecutive cinema sessions are free (XTRA TIME / Extra Time). Only call when customer explicitly asks for double/Extra Time.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "date": {
                            "type": "STRING",
                            "description": "Date in YYYY-MM-DD format."
                        },
                        "first_session_index": {
                            "type": "INTEGER",
                            "description": "Index (0-4) of the first of two consecutive sessions."
                        }
                    },
                    "required": ["date", "first_session_index"]
                }
            },
            {
                "name": "send_menu_image",
                "description": "Send cinema menu image to customer. Only call when customer explicitly asks about menu/packages/prices/how much. NEVER call when customer mentions a date or session.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
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


def execute_tool(name, args, sender_id=None):
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

        if name == "send_menu_image":
            if not sender_id:
                return {"error": "No recipient", "error_type": "config"}
            from services.instagram import send_image
            image_url = "https://raw.githubusercontent.com/kristophershola/lavish-booking-bot/main/static/menu.png"
            response = send_image(sender_id, image_url)
            if "error" in response:
                print(f"SEND MENU IMAGE FAILED: {response['error']}")
                return {"sent": False, "error": str(response["error"].get("message", "Upload failed"))}
            return {"sent": True}

        return {"error": f"Unknown tool: {name}", "error_type": "unknown_tool"}

    except ValueError as exc:
        # Date format errors
        print(f"TOOL DATE FORMAT ERROR for {name} with args {args}: {exc}")
        return {"error": "Invalid date format. Use YYYY-MM-DD.", "error_type": "date_format"}
    except Exception as exc:
        print(f"TOOL EXECUTION ERROR for {name} with args {args}: {exc}")
        return {"error": "Something went wrong checking that, please try again in a moment.", "error_type": "execution"}
