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
    """Wraps the Sheets API 'Get Values' call, using A1 notation ranges,
    per the project note that this is the correct approach over
    'Get Sheets Info'.
    """
    service = get_sheets_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_range
    ).execute()
    return result.get("values", [])


def debug_dump_tab(tab_name, max_rows=8):
    """Temporary helper, not for production use. Fetches the first several
    rows of a tab as raw values so we can confirm the real header layout
    and date formatting before finalizing the parsing logic below.
    """
    values = get_values(f"'{tab_name}'!A1:Z{max_rows}")
    return values


# ---------------------------------------------------------------------
# Everything below this line assumes the column layout described in the
# project specification, but has not yet been confirmed against the real
# sheet. Do not rely on these until debug_dump_tab() output has been
# checked for both an apartment tab and a hall tab.
# ---------------------------------------------------------------------

def get_apartment_tab_rows(unit_tab):
    """Returns all rows for one apartment tab (A1 through C2), including
    the header row as rows[0].
    Expected columns per the spec: Day, Date, AVAILABILITY, CHANNEL, GUEST NAME
    """
    return get_values(f"'{unit_tab}'!A1:E1000")


def get_hall_tab_rows(hall_tab):
    """Returns all rows for one hall tab (HALL 1 or HALL 2), including the
    header row as rows[0].
    Expected columns per the spec: Date, then 6 session columns.
    """
    return get_values(f"'{hall_tab}'!A1:G1000")
