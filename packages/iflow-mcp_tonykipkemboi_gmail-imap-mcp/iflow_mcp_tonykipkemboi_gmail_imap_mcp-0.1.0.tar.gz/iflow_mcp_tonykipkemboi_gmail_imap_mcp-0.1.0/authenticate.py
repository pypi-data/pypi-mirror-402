#!/usr/bin/env python3
"""
Simple script to authenticate with Gmail.
This will create the necessary token file in the credentials directory.
"""
import sys
import os
from pathlib import Path

# Add the project directory to the path so we can import the module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from gmail_imap_mcp.auth import GmailAuthManager

def main():
    if len(sys.argv) < 2:
        print("Usage: python authenticate.py iamtonykipkemboi@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"Authenticating {email}...")
    
    # Use the same credentials directory as the MCP server
    home_dir = str(Path.home())
    credentials_dir = os.path.join(home_dir, ".gmail_imap_mcp_credentials")
    
    auth_manager = GmailAuthManager(credentials_dir)
    success = auth_manager.authenticate(email)
    
    if success:
        print(f"Authentication successful for {email}")
        print(f"Token saved to {credentials_dir}")
    else:
        print(f"Authentication failed for {email}")
        sys.exit(1)

if __name__ == "__main__":
    main()
