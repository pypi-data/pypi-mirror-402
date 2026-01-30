"""
Authentication module for Gmail IMAP MCP server.
Handles OAuth2 authentication with Gmail.
"""
import os
import json
import pickle
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Define scopes needed for Gmail access
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]

class GmailAuthManager:
    """Manages authentication for Gmail accounts."""
    
    def __init__(self, credentials_dir: str = None):
        """
        Initialize the authentication manager.
        
        Args:
            credentials_dir: Directory to store credentials
        """
        if credentials_dir is None:
            # Use user's home directory to store credentials
            home_dir = str(Path.home())
            credentials_dir = os.path.join(home_dir, ".gmail_imap_mcp_credentials")
            
        self.credentials_dir = Path(credentials_dir)
        print(f"Using credentials directory: {self.credentials_dir}", file=sys.stderr)
        self.credentials_dir.mkdir(exist_ok=True)
        self.client_secret_path = self.credentials_dir / "client_secret.json"
        print(f"Client secret path: {self.client_secret_path}", file=sys.stderr)
        print(f"Client secret exists: {self.client_secret_path.exists()}", file=sys.stderr)
        
    def get_credentials(self, email: str) -> Optional[Credentials]:
        """
        Get credentials for a specific Gmail account.
        
        Args:
            email: Email address to get credentials for
            
        Returns:
            Credentials object if available, None otherwise
        """
        token_path = self.credentials_dir / f"{email.replace('@', '_at_')}_token.pickle"
        print(f"Looking for token at: {token_path}", file=sys.stderr)
        
        creds = None
        # Load existing credentials if available
        if token_path.exists():
            print(f"Found existing token for {email}", file=sys.stderr)
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                print(f"Loaded credentials from token file", file=sys.stderr)
            except Exception as e:
                print(f"Error loading token: {e}", file=sys.stderr)
                
        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print(f"Refreshing expired token for {email}", file=sys.stderr)
                try:
                    creds.refresh(Request())
                    print(f"Token refreshed successfully", file=sys.stderr)
                except Exception as e:
                    print(f"Error refreshing token: {e}", file=sys.stderr)
                    creds = None
            
            if not creds:
                if not self.client_secret_path.exists():
                    print(f"Error: Client secret file not found at {self.client_secret_path}", file=sys.stderr)
                    return None
                
                print(f"Starting new authentication flow for {email}", file=sys.stderr)
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_path, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    print(f"Authentication successful for {email}", file=sys.stderr)
                except Exception as e:
                    print(f"Error during authentication flow: {e}", file=sys.stderr)
                    return None
                
            # Save the credentials for the next run
            try:
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
                print(f"Saved new token for {email} at {token_path}", file=sys.stderr)
            except Exception as e:
                print(f"Error saving token: {e}", file=sys.stderr)
                
        return creds
    
    def authenticate(self, email: str) -> bool:
        """
        Authenticate a Gmail account.
        
        Args:
            email: Email address to authenticate
            
        Returns:
            True if authentication successful, False otherwise
        """
        print(f"Authenticating {email}...", file=sys.stderr)
        creds = self.get_credentials(email)
        return creds is not None
    
    def list_authenticated_accounts(self) -> list[str]:
        """
        List all authenticated Gmail accounts.
        
        Returns:
            List of authenticated email addresses
        """
        accounts = []
        for file in self.credentials_dir.glob("*_token.pickle"):
            email = file.name.replace("_at_", "@").replace("_token.pickle", "")
            accounts.append(email)
        return accounts
