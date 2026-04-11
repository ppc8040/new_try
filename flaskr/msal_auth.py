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

# driveItem ID-based base URL for Excel worksheet API (does not use /content)
US_INVENTORY_WORKBOOK_URL = 'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/drives/b!f3YcIMyT70u3bEeicXBljfkhSwoN1sNHp1E7IXoYuY6pKksmpTZO4LBBqxehiLiu/items/01QYIYROF6Y2GOVW7725BZO354PWSELRRZ'

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


def _get_drive_item_id():
    """
    Resolves the driveItem ID for the US_Inventory file by following the
    redirect from the /content endpoint. Returns the driveItem ID string.
    """
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    # HEAD request on /content returns a redirect; we need the driveItem metadata instead
    meta_url = (
        'https://graph.microsoft.com/v1.0/sites/'
        '201c767f-23cc-4eff-b76c-47a275706531,'
        '094b21f9-6ed4-47c3-a751-3b217a18b98e'
        '/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98'
        '/items/3/driveItem'
    )
    resp = requests.get(meta_url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to get driveItem metadata. Status: {resp.status_code}, {resp.text}")
    data = resp.json()
    parent_ref = data.get('parentReference', {})
    drive_id   = parent_ref.get('driveId', '')
    item_id    = data.get('id', '')
    if not drive_id or not item_id:
        raise Exception(f"Could not extract driveId/itemId from metadata: {data}")
    return drive_id, item_id


def append_to_release_tracker(release_id, username, rows):
    """
    Appends new rows to the 'Portal Release Tracker' sheet of the US_Inventory
    Excel file using the Microsoft Graph API Excel worksheets/rows endpoint.
    This avoids downloading and re-uploading the whole workbook with openpyxl,
    which was silently corrupting or failing on the file.

    Each item in `rows` is a dict with keys:
        customer_part, indus_part, customer_po, quantity
    """
    token       = get_access_token()
    auth_header = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    # --- Step 1: resolve the driveId and itemId dynamically ---
    drive_id, item_id = _get_drive_item_id()

    workbook_base = (
        f'https://graph.microsoft.com/v1.0'
        f'/drives/{drive_id}/items/{item_id}/workbook'
    )

    # --- Step 2: find the used range to determine next empty row ---
    sheet_name_encoded = 'Portal%20Release%20Tracker'
    used_range_url = f"{workbook_base}/worksheets/{sheet_name_encoded}/usedRange"
    ur = requests.get(used_range_url, headers=auth_header)
    if ur.status_code != 200:
        raise Exception(f"Failed to get usedRange. Status: {ur.status_code}, {ur.text}")

    used_data    = ur.json()
    used_address = used_data.get('address', '')
    # address is like "Portal Release Tracker!A1:J42" — extract last row number
    try:
        cell_range   = used_address.split('!')[-1]          # e.g. "A1:J42"
        last_row_str = ''.join(filter(str.isdigit, cell_range.split(':')[-1]))  # "42"
        last_row     = int(last_row_str)
    except Exception:
        last_row = 1  # fallback: treat as only header row present

    # --- Step 3: format date ---
    date_of_request = datetime.now().strftime('%d-%b-%y')

    # --- Step 4: append one row per item via /range(address) PATCH ---
    for i, row in enumerate(rows):
        target_row = last_row + 1 + i
        # Columns A-J (1-10)
        range_address = f'A{target_row}:J{target_row}'
        range_url     = f"{workbook_base}/worksheets/{sheet_name_encoded}/range(address='{range_address}')"

        row_values = [[
            release_id,
            username,
            date_of_request,
            row.get('customer_part') or '',
            row.get('indus_part')    or '',
            row.get('customer_po')   or '',
            row.get('quantity')      if row.get('quantity') is not None else '',
            'Pending',
            '',   # Invoice no.
            ''    # PL no.
        ]]

        patch_resp = requests.patch(
            range_url,
            headers=auth_header,
            json={'values': row_values}
        )
        if patch_resp.status_code not in (200, 201):
            raise Exception(
                f"Failed to write row {target_row} to tracker. "
                f"Status: {patch_resp.status_code}, {patch_resp.text}"
            )
