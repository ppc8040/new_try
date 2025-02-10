import io
import msal
import pandas as pd
import requests
import json

SCOPES = ["https://graph.microsoft.com/.default"]
sharepoint_site_url = 'https://indusair.sharepoint.com'    

class AuthConfig:
    CLIENT_ID1 = '785b5fc9-1624-458d-90cb-a140dff579c7'
    CLIENT_SECRET1 = 'Zcw8Q~YSEqXPypF4Gn_mNVpp2MVPRMM.95hjVdbP'
    TENANT_ID1 = 'ed97e9bb-e119-4bd4-ab00-307d64bdf908'
    AUTHORITY1 = f'https://login.microsoftonline.com/ed97e9bb-e119-4bd4-ab00-307d64bdf908'

authority = AuthConfig.AUTHORITY1

# Function to get an access token
def get_access_token():
    auth_config = AuthConfig()
    app = msal.ConfidentialClientApplication(
        auth_config.CLIENT_ID1, authority=authority, client_credential=auth_config.CLIENT_SECRET1
    )
    result = app.acquire_token_silent(scopes=SCOPES, account=None)
    
    if not result:
        result = app.acquire_token_for_client(scopes=SCOPES)
    
    if 'access_token' in result:
        return result['access_token']
    else:
        raise Exception("Failed to acquire access token.")

# Function to send email via Microsoft Graph API
def send_email_graph_api(recipients, subject, body):
    try:
        access_token = get_access_token()

        # Define email structure
        email_message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [{"emailAddress": {"address": email}} for email in recipients]
            }
        }

        # Make the API request
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        url = "https://graph.microsoft.com/v1.0/users/releases@indusair.ae/sendMail"
        response = requests.post(url, headers=headers, data=json.dumps(email_message))

        # Check response status
        if response.status_code == 202:
            return {"status": "success", "message": "Email sent successfully."}
        else:
            return {"status": "error", "message": f"Failed to send email. Status Code: {response.status_code}, Response: {response.text}"}

    except Exception as e:
        return {"status": "error", "message": f"Exception occurred: {str(e)}"}
