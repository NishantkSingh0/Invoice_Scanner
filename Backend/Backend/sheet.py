import json
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
import re
load_dotenv()

GOOGLE_CREDENTIAL = os.getenv('GOOGLE_CREDENTIAL')
if GOOGLE_CREDENTIAL:
    try:
        parsed = json.loads(GOOGLE_CREDENTIAL)
        if isinstance(parsed, dict) and parsed.get('private_key'):
            parsed['private_key'] = parsed['private_key'].replace('\\n', '\n')
        CREDENTIALS = parsed
    except (TypeError, json.JSONDecodeError):
        CREDENTIALS = Path(__file__).resolve().parent / 'credentials.json'
else:
    CREDENTIALS = Path(__file__).resolve().parent / 'credentials.json'


def hex_to_rgb(hex_color):
    """
    Convert HEX color to Google Sheets RGB format.
    Example: #f9ede8
    """

    hex_color = hex_color.lstrip('#')

    return {
        "red": int(hex_color[0:2], 16) / 255,
        "green": int(hex_color[2:4], 16) / 255,
        "blue": int(hex_color[4:6], 16) / 255
    }


def fill_sheet(
    json_data,
    SheetID: str,
    sheet_name='Sheet1',
    header_row=1,
    highlight_columns=None
):
    """
    Fills a Google Sheet with JSON data for one row
    and optionally highlights specific columns in the inserted row.

    Args:
        json_data (dict): Dictionary with column names as keys.
        SheetID (str): Google Sheet ID.
        sheet_name (str): Sheet tab name.
        header_row (int): Header row number.
        highlight_columns (list): List of column names to highlight.

    Returns:
        bool
    """

    sheet_id = SheetID

    try:

        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID environment variable is required")

        # Load credentials
        if isinstance(CREDENTIALS, dict):

            if not CREDENTIALS.get('private_key'):
                raise ValueError('Service account JSON is missing private_key')

            creds = Credentials.from_service_account_info(
                CREDENTIALS,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        else:

            if not CREDENTIALS.exists():
                raise FileNotFoundError(
                    f"Service account credentials file not found: {CREDENTIALS}"
                )

            creds = Credentials.from_service_account_file(
                str(CREDENTIALS),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        # Build service
        service = build('sheets', 'v4', credentials=creds)

        # Read headers
        header_range = f'{sheet_name}!A{header_row}:ZZ{header_row}'

        print("Header range: ", header_range)

        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=header_range
        ).execute()

        headers = result.get('values', [[]])[0]

        if not headers:
            print("No headers found in the sheet.")
            return False

        # Create row
        row = []

        for header in headers:

            try:

                value = json_data.get(header, '')

                # Convert Exception object
                if isinstance(value, Exception):

                    value = f"[VALUE ERROR]: {str(value)}"

                # Convert unsupported types
                elif not isinstance(value, (str, int, float, bool, type(None))):

                    value = str(value)

                row.append(value)

            except Exception as e:

                error_msg = f"[COLUMN ERROR: {header}] {str(e)}"

                print(error_msg)

                row.append(error_msg)

        # Append row
        append_range = f'{sheet_name}!A:A'

        body = {
            'values': [row]
        }

        append_response = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=append_range,
            valueInputOption='RAW',
            body=body
        ).execute()

        # ===============================
        # Highlight Specific Columns
        # ===============================

        if highlight_columns:

            # Get inserted row number
            updated_range = append_response['updates']['updatedRange']

            # Example:
            # Sheet1!A5:Z5

            row_number = int(re.findall(r'\d+', updated_range)[0])

            # Get sheet metadata
            sheet_metadata = service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()

            sheetId = None

            for sheet in sheet_metadata['sheets']:

                if sheet['properties']['title'] == sheet_name:
                    sheetId = sheet['properties']['sheetId']
                    break

            if sheetId is not None:

                requests = []

                for column_name in highlight_columns:

                    if column_name not in headers:
                        continue

                    col_idx = headers.index(column_name)

                    requests.append({
                        "repeatCell": {
                            "range": {
                                "sheetId": sheetId,
                                "startRowIndex": row_number - 1,
                                "endRowIndex": row_number,
                                "startColumnIndex": col_idx,
                                "endColumnIndex": col_idx + 1
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": hex_to_rgb("#fefbe6")
                                }
                            },
                            "fields": "userEnteredFormat.backgroundColor"
                        }
                    })

                if requests:

                    service.spreadsheets().batchUpdate(
                        spreadsheetId=sheet_id,
                        body={"requests": requests}
                    ).execute()

        return True

    except Exception as e:

        print(f"Error filling sheet: {e}")

        return False



def fill_sheet_bulk(json_data_list, SheetID, sheet_name='Sheet1', header_row=1):
    """
    Push multiple rows to Google Sheet at once.

    Args:
        json_data_list (list): List of dictionaries
        SheetID (str): Google Sheet ID
        sheet_name (str): Sheet tab name

    Returns:
        bool
    """

    try:

        # Credentials
        if isinstance(CREDENTIALS, dict):

            creds = Credentials.from_service_account_info(
                CREDENTIALS,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        else:

            creds = Credentials.from_service_account_file(
                str(CREDENTIALS),
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )

        # Build service
        service = build('sheets', 'v4', credentials=creds)

        # Read headers
        header_range = f'{sheet_name}!A{header_row}:ZZ{header_row}'
        print("Header range: ",header_range)
        result = service.spreadsheets().values().get(
            spreadsheetId=SheetID,
            range=header_range
        ).execute()

        headers = result.get('values', [[]])[0]

        if not headers:
            raise ValueError("No headers found in sheet")

        # Convert dicts into rows
        rows = []

        for json_data in json_data_list:

            row = []

            for header in headers:
                row.append(json_data.get(header, ''))

            rows.append(row)

        # Bulk append
        body = {
            'values': rows
        }

        service.spreadsheets().values().append(
            spreadsheetId=SheetID,
            range=f'{sheet_name}!A:A',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

        return True

    except Exception as e:
        print(f"Error filling sheet: {e}")
        return False