# Google Sheets integration, Phase 3 work.
#
# Sheet structure (from the project specification):
#   Apartment tabs (A1 through C2): Day, Date, AVAILABILITY, CHANNEL, GUEST NAME
#   Hall tabs (HALL 1, HALL 2): one row per date, 6 session columns
#   CINEMA 1 and CINEMA 2 tabs are legacy and should be ignored
#
# This module will be read-only. The bot never writes to the sheet itself,
# staff make all reservation edits after payment is verified.


def get_sheet_values(spreadsheet_id, sheet_range):
    """Wraps the Google Sheets API 'Get Values' call. Not yet implemented."""
    raise NotImplementedError("Google Sheets integration not yet built, see Phase 3 in project plan.")


def find_row_for_date(sheet_values, target_date):
    """Two-step lookup: find the correct date row first, then read the
    relevant availability cells from that row. Not yet implemented.
    """
    raise NotImplementedError("Google Sheets integration not yet built, see Phase 3 in project plan.")
