from __future__ import print_function

import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Constants
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
APPLICATION_NAME = "Gmail API Python"


class GmailClient:
    """Handles authentication and service creation for Gmail API."""

    def __init__(self):
        self.creds = self._get_credentials()
        self.service = self._create_service()

    def _get_credentials(self) -> Credentials:
        """Get user credentials for Gmail API access."""
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return creds

    def _create_service(self):
        """Build a Gmail service object."""
        return build("gmail", "v1", credentials=self.creds)
