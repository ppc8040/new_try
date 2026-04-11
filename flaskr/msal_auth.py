import io
import msal
import pandas as pd
import requests
import openpyxl
from datetime import datetime

from flaskr.auth_config import AuthConfig

authority = 'https://login.microsoftonline.com/ed97e9bb-e119-4bd4-ab00-307d64bdf908'

# SharePoint Parameters
sharepoint_site_url = 'https://indusair.sharepoint.com'

# Graph API URL for US_Inventory Excel file (driveItem content endpoint)
US_INVENTORY_GRAPH_URL = 'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/3/driveItem/content'

# Hardcoded workbook base URL — skips the driveItem metadata lookup entirely.
# Derived from the list-item driveItem endpoint; stable as long as the file
# is not moved or replaced in SharePoint.
_WORKBOOK_BASE = (
    'https://graph.microsoft.com/v1.0'
    '/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e'
    '/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98'
    '/items/3/driveItem/workbook'
)
_TRACKER_SHEET = 'Portal%20Release%20Tracker'


# Function to get an access token
def get_access_token():
    auth_config = AuthConfig()
    app = msal.ConfidentialClientApplication(
        auth_config.CLIENT_ID, authority=authority, client_credential=auth_config.CLIENT_SECRET
    )
    result = app.acquire_token_silent(scopes=['https://graph.microsoft.com/.default'], account=None)

    if not result:
        result = app.acquire_token_for_client(scopes=['https://graph.microsoft.com/.default'])

    if 'access_token' in result:
        return result['access_token']
    else:
        raise Exception("Failed to acquire access token.")


# Function to fetch the Excel file from SharePoint
def fetch_excel_data(sheet_name, header=0, usecols=None):
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(US_INVENTORY_GRAPH_URL, headers=headers)
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name=sheet_name, header=header, usecols=usecols)
        return df
    else:
        raise Exception(f"Failed to fetch Excel file. Status code: {response.status_code}, Response: {response.text}")


def fetch_oor_data(sheet_name, header=0, usecols=None):
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    graph_url = 'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/14/driveItem/content'

    response = requests.get(graph_url, headers=headers)
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name=sheet_name, header=header, usecols=usecols)
        return df
    else:
        raise Exception(f"Failed to fetch Excel file. Status code: {response.status_code}, Response: {response.text}")


def upload_excel_file(file_bytes):
    """
    Uploads the modified Excel file bytes back to SharePoint via Microsoft Graph API (PUT).
    Overwrites the existing file in-place.
    """
    token = get_access_token()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    response = requests.put(US_INVENTORY_GRAPH_URL, headers=headers, data=file_bytes)
    if response.status_code not in (200, 201):
        raise Exception(f"Failed to upload Excel file. Status code: {response.status_code}, Response: {response.text}")


def append_to_release_tracker(release_id, username, rows):
    """
    Appends new rows to the 'Portal Release Tracker' sheet using the
    Graph API Excel workbook/worksheets/range PATCH endpoint.

    Optimisations vs previous version:
      - Hardcoded _WORKBOOK_BASE skips the driveItem metadata round-trip.
      - All rows are written in a SINGLE PATCH call (one range covering
        all rows at once) instead of one PATCH per row.

    Each item in `rows` is a dict with keys:
        customer_part, indus_part, customer_po, quantity
    """
    token       = get_access_token()
    auth_header = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # --- Step 1: find the last used row (1 API call) ---
    used_range_url = f"{_WORKBOOK_BASE}/worksheets/{_TRACKER_SHEET}/usedRange"
    ur = requests.get(used_range_url, headers=auth_header)
    if ur.status_code != 200:
        raise Exception(f"Failed to get usedRange. Status: {ur.status_code}, {ur.text}")

    used_address = ur.json().get('address', '')
    try:
        cell_range   = used_address.split('!')[-1]            # e.g. "A1:J42"
        last_row_str = ''.join(filter(str.isdigit, cell_range.split(':')[-1]))  # "42"
        last_row     = int(last_row_str)
    except Exception:
        last_row = 1  # fallback: only header row present

    # --- Step 2: build all row values ---
    date_of_request = datetime.now().strftime('%d-%b-%y')
    first_new_row   = last_row + 1
    last_new_row    = last_row + len(rows)

    all_values = [
        [
            release_id,
            username,
            date_of_request,
            row.get('customer_part') or '',
            row.get('indus_part')    or '',
            row.get('customer_po')   or '',
            row.get('quantity') if row.get('quantity') is not None else '',
            'Pending',
            '',   # Invoice no.
            ''    # PL no.
        ]
        for row in rows
    ]

    # --- Step 3: single PATCH for all rows at once ---
    range_address = f'A{first_new_row}:J{last_new_row}'
    range_url     = f"{_WORKBOOK_BASE}/worksheets/{_TRACKER_SHEET}/range(address='{range_address}')"

    patch_resp = requests.patch(
        range_url,
        headers=auth_header,
        json={'values': all_values}
    )
    if patch_resp.status_code not in (200, 201):
        raise Exception(
            f"Failed to write rows to tracker. "
            f"Status: {patch_resp.status_code}, {patch_resp.text}"
        )
