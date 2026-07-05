import json

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import GOOGLE_SERVICE_ACCOUNT_JSON, SPREADSHEET_ID, APARTMENT_TABS, HALL_TABS

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

_sheets_service = None


def get_sheets_service():
    """Builds (and caches) an authorized Sheets API client from the service
    account JSON stored in the GOOGLE_SERVICE_ACCOUNT_JSON environment
    variable.
    """
    global _sheets_service
    if _sheets_service is not None:
        return _sheets_service

    if not GOOGLE_SERVICE_ACCOUNT_JSON:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not set")

    info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    _sheets_service = build("sheets", "v4", credentials=credentials)
    return _sheets_service


def get_values(sheet_range):
    """Wraps the Sheets API 'Get Values' call, using A1 notation ranges."""
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range
    ).execute()
    return result.get("values", [])


def debug_dump_tab(tab_name, max_rows=50):
    """Temporary helper, not for production use."""
    return get_values(f"'{tab_name}'!A1:Z{max_rows}")


def get_apartment_tab_rows(unit_tab):
    """Returns all rows for one apartment tab (A1 through C2).

    Confirmed real structure: header row is ["", "MONTH NAME", "AVAILABILITY",
    "CHANNEL", "GUEST NAME"]. Each following row is [weekday, day-of-month]
    when available, or [weekday, day-of-month, "BOOKED", channel, guest name]
    when booked. A tab may contain more than one month, each new month
    starting with another header row where column B holds the month name.
    """
    return get_values(f"'{unit_tab}'!A1:E1000")


def get_hall_tab_rows(hall_tab):
    """Returns all rows for one hall tab (HALL 1 or HALL 2). Structure not
    yet confirmed against the real sheet, pending a debug dump.
    """
    return get_values(f"'{hall_tab}'!A1:G1000")


def _parse_apartment_tab_for_date(rows, target_date):
    """Walks one apartment tab's rows and determines whether target_date is
    booked. Tracks the current month as it moves down the sheet, since a
    single tab can contain more than one month's block of rows.

    Returns True if booked, False if available, or None if this tab has no
    row at all for that date (treated the same as available by callers,
    since a missing row means nothing has ever been recorded against it).
    """
    target_month = target_date.strftime("%B").upper()
    target_day = str(target_date.day)
    current_month = None

    for row in rows:
        if not row:
            continue

        col_a = row[0] if len(row) > 0 else ""
        col_b = row[1] if len(row) > 1 else ""

        # A header row has an empty first column and a month name (not a
        # number) in the second column.
        if col_a == "" and col_b and not str(col_b).strip().isdigit():
            current_month = str(col_b).strip().upper()
            continue

        if current_month != target_month:
            continue

        if str(col_b).strip() == target_day:
            availability = row[2].strip().upper() if len(row) > 2 and row[2] else ""
            return availability == "BOOKED"

    return None


def check_any_apartment_available(target_date):
    """Scans every apartment tab, never stopping at the first BOOKED result,
    since a booking in one unit does not affect the others. Returns a tuple
    of (is_available, list_of_available_unit_tabs). The unit list is for
    internal use only, it must never be shown to a customer.
    """
    available_units = []
    for tab in APARTMENT_TABS:
        rows = get_apartment_tab_rows(tab)
        booked = _parse_apartment_tab_for_date(rows, target_date)
        if booked is not True:
            available_units.append(tab)
    return (len(available_units) > 0, available_units)


def _target_date_variants(target_date):
    """Hall tab dates are written like '1-Jul', with one confirmed anomaly
    seen as 'Jul 31'. This builds both forms, lowercased, so a row can be
    matched regardless of which style was used for that particular cell.
    """
    day = str(target_date.day)
    month_abbr = target_date.strftime("%b")
    return {
        f"{day}-{month_abbr}".lower(),
        f"{month_abbr} {day}".lower(),
    }


def _get_session_value(rows, target_date, session_index):
    """Looks up one hall tab's row for target_date, then returns the raw
    value in the given session column (0 through 5, matching the 6 daily
    sessions in order). Returns "" if that session is free, the package
    shortcode or 'XTRA TIME' string if occupied, or None if this tab has
    no row at all for that date.
    """
    variants = _target_date_variants(target_date)

    for row in rows[1:]:  # skip header row
        if not row:
            continue
        date_cell = str(row[0]).strip().lower()
        if date_cell not in variants:
            continue

        column_index = session_index + 1  # column 0 is the date itself
        if column_index < len(row) and row[column_index]:
            return row[column_index].strip()
        return ""

    return None


def is_session_available(rows, target_date, session_index):
    """True if free, False if occupied (any shortcode or XTRA TIME), or
    None if the date row itself was not found in this tab.
    """
    value = _get_session_value(rows, target_date, session_index)
    if value is None:
        return None
    return value == ""
