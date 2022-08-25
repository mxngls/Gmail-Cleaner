from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.pickle.
# Set the scope and application name.

SCOPES = ['https://mail.google.com/']
APPLICATION_NAME = 'Gmail API Python'

# Deletes all the e-mails sent from a specific adress that us chosen by the user.
  
class GmailClient:
    def __init__(self):
        self.creds = self.get_credentials()
        self.service = self.service()
            

    def get_credentials(self):

        creds = None
        '''
        The file token.pickle stores the user's access and refresh tokens, and is
        created automatically when the authorization flow completes for the first
        time.
        '''

        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return creds

    # Builds a G-Mail service object.

    def service(self):
        service = build('gmail', 'v1', credentials=self.creds)
        return service