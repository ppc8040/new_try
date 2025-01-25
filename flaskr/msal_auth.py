import io
import msal
import pandas as pd
import requests

from flaskr.auth_config import AuthConfig

authority = 'https://login.microsoftonline.com/ed97e9bb-e119-4bd4-ab00-307d64bdf908'

# SharePoint Parameters
sharepoint_site_url = 'https://indusair.sharepoint.com'      # Replace with your site ID
#drive_item_path = '/sites/testruk/folder1/Book.xlsx'        # Path to the Excel file in SharePoint

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
def fetch_excel_data(sheet_name,header=0, usecols =None ):
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Construct the Microsoft Graph API URL for the Excel file content
    graph_url = f'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/3/driveItem/content'
    
    response = requests.get(graph_url, headers=headers)
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name=sheet_name, header= header, usecols=usecols)
        return df
    else:
        raise Exception(f"Failed to fetch Excel file. Status code: {response.status_code}, Response: {response.text}")

def fetch_oor_data(sheet_name,header=0, usecols =None ):
    token = get_access_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    # Construct the Microsoft Graph API URL for the Excel file content
    graph_url = f'https://graph.microsoft.com/v1.0/sites/201c767f-23cc-4eff-b76c-47a275706531,094b21f9-6ed4-47c3-a751-3b217a18b98e/lists/4a2ba029-6536-4e0b-abf6-e0a1facddf98/items/6/driveItem/content'
    
    response = requests.get(graph_url, headers=headers)
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)
        df = pd.read_excel(excel_data, sheet_name=sheet_name, header= header, usecols=usecols)
        return df
    else:
        raise Exception(f"Failed to fetch Excel file. Status code: {response.status_code}, Response: {response.text}")


