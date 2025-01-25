import os


class AuthConfig:
    CLIENT_ID = os.environ.get('CLIENT_ID')  
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET') 
