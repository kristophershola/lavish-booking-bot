MAIN_MENU = {
    "text": "Welcome to Lavish! How can we help you?",
    "buttons": [
        {"title": "Book an Apartment", "payload": "BOOK_APARTMENT"},
        {"title": "Book Cinema", "payload": "BOOK_CINEMA"},
        {"title": "Something Else?", "payload": "SOMETHING_ELSE"},
    ]
}

QUIET_OR_PARTY = {
    "text": "Will this be a quiet stay or a party?",
    "buttons": [
        {"title": "Quiet Stay", "payload": "QUIET_STAY"},
        {"title": "Party", "payload": "PARTY"},
    ]
}

RESPONSES = {
    "BOOK_APARTMENT": None,
    "QUIET_STAY": None,
    "PARTY": None,
    "BOOK_CINEMA": "What date(s) would you like to book? So we can check availability",
    "SOMETHING_ELSE": "We're setting up our FAQ section. In the meantime, feel free to ask me anything!",
}
