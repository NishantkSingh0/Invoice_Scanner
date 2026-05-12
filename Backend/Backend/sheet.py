import json
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
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


def fill_sheet(json_data, SheetID: str, sheet_name='Sheet1', header_row=1):
    """
    Fills a Google Sheet with JSON data for one row.
    
    Args:
        json_data (dict): Dictionary with column names as keys and values to fill.
        sheet_name (str): Name of the sheet tab (default: 'Sheet1').
    
    Returns:
        bool: True if successful, False otherwise.
    """
    sheet_id = SheetID
    try:
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID environment variable is required")

        # Load credentials
        if isinstance(CREDENTIALS, dict):
            # print(f"fill_sheet: using env credentials dict, client_email={CREDENTIALS.get('client_email')}")
            if not CREDENTIALS.get('private_key'):
                raise ValueError('Service account JSON is missing private_key')
            # print(f"fill_sheet: private_key length={len(CREDENTIALS.get('private_key', ''))}")
            creds = Credentials.from_service_account_info(CREDENTIALS, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        else:
            # print(f"fill_sheet: using local credentials file path={CREDENTIALS}")
            if not CREDENTIALS.exists():
                raise FileNotFoundError(f"Service account credentials file not found: {CREDENTIALS}")
            creds = Credentials.from_service_account_file(str(CREDENTIALS), scopes=['https://www.googleapis.com/auth/spreadsheets'])
        
        # Build the service
        service = build('sheets', 'v4', credentials=creds)
        
        # Read the header row to get column names
        header_range = f'{sheet_name}!A{header_row}:ZZ{header_row}'
        print("Header range: ",header_range)
        result = service.spreadsheets().values().get(spreadsheetId=sheet_id, range=header_range).execute()
        headers = result.get('values', [[]])[0]
        
        if not headers:
            print("No headers found in the sheet.")
            return False
        
        # Create the row data based on headers
        row = []
        for header in headers:
            row.append(json_data.get(header, ''))
        
        # Append the row to the sheet
        append_range = f'{sheet_name}!A:A'
        body = {
            'values': [row]
        }
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=append_range,
            valueInputOption='RAW',
            body=body
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