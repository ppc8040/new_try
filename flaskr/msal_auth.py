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

# Graph API URL for US_Inventory Excel file
US_INVENTORY_GRAPH_URL = 'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/3/driveItem/content'

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
    
    # Construct the Microsoft Graph API URL for the Excel file content
    graph_url = f'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/14/driveItem/content'
    
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
    Downloads the US_Inventory Excel file, appends new rows to the
    'Portal Release Tracker' sheet only, and uploads it back.

    Each item in `rows` is a dict with keys:
        customer_part, indus_part, customer_po, quantity

    Other sheets are never read or modified.
    """
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}

    # Download the full Excel file as binary
    response = requests.get(US_INVENTORY_GRAPH_URL, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to download Excel for tracker update. Status: {response.status_code}")

    # Open with openpyxl — preserves all other sheets byte-for-byte
    workbook = openpyxl.load_workbook(io.BytesIO(response.content))

    # Target only the Portal Release Tracker sheet
    sheet = workbook['Portal Release Tracker']

    # Find the next empty row (after header row 1)
    next_row = sheet.max_row + 1
    # Handle case where sheet has only the header and max_row returns 1
    # Walk back to find actual last filled row to avoid blank row gaps
    while next_row > 2 and all(sheet.cell(row=next_row - 1, column=c).value is None for c in range(1, 11)):
        next_row -= 1

    # Format date as 11-Apr-26
    date_of_request = datetime.now().strftime('%d-%b-%y')

    # Append one row per line item
    for row in rows:
        sheet.cell(row=next_row, column=1).value  = release_id              # ReleaseID
        sheet.cell(row=next_row, column=2).value  = username                # Customer Code
        sheet.cell(row=next_row, column=3).value  = date_of_request         # Date of Request
        sheet.cell(row=next_row, column=4).value  = row['customer_part']    # Customer Part
        sheet.cell(row=next_row, column=5).value  = row['indus_part']       # Indus Part
        sheet.cell(row=next_row, column=6).value  = row['customer_po']      # Customer PO# (blank if no PO)
        sheet.cell(row=next_row, column=7).value  = row['quantity']         # Quantity for Release
        sheet.cell(row=next_row, column=8).value  = 'Pending'               # Release Status
        sheet.cell(row=next_row, column=9).value  = None                    # Invoice no. (untouched)
        sheet.cell(row=next_row, column=10).value = None                    # PL no. (untouched)
        next_row += 1

    # Save workbook back to bytes in memory
    output = io.BytesIO()
    workbook.save(output)
    output.seek(0)

    # Upload back to SharePoint
    upload_excel_file(output.read())
