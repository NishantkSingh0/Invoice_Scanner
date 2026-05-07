import json
from pathlib import Path
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import os
load_dotenv()

CREDENTIALS = json.loads(os.getenv('GOOGLE_CREDENTIAL'))
if not CREDENTIALS:
    CREDENTIALS = str(Path(__file__).resolve().parent / 'credentials.json')


def fill_sheet(json_data, sheet_name='Sheet1'):
    """
    Fills a Google Sheet with JSON data for one row.
    
    Args:
        json_data (dict): Dictionary with column names as keys and values to fill.
        sheet_name (str): Name of the sheet tab (default: 'Sheet1').
    
    Returns:
        bool: True if successful, False otherwise.
    """
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    try:
        # Load credentials
        creds = Credentials.from_service_account_file(CREDENTIALS, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        
        # Build the service
        service = build('sheets', 'v4', credentials=creds)
        
        # Read the header row to get column names
        header_range = f'{sheet_name}!1:1'
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