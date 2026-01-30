import asyncio
import os
import json
from typing import Dict, List, Optional, Any
import re
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
from pydantic import AnyUrl, BaseModel
import mcp.server.stdio

from .auth import GmailAuthManager
from .imap_client import GmailImapClient

# Create auth manager
auth_manager = GmailAuthManager()

# Store active connections
email_clients: Dict[str, GmailImapClient] = {}

server = Server("gmail-imap-mcp")

class EmailResource(BaseModel):
    """Model representing an email resource."""
    email_id: str
    mailbox: str
    account: str
    subject: str

# Store email resources
email_resources: Dict[str, EmailResource] = {}

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """
    List available email resources.
    Each email is exposed as a resource with a custom email:// URI scheme.
    """
    resources = []
    
    # Add account resources
    for account in auth_manager.list_authenticated_accounts():
        resources.append(
            types.Resource(
                uri=AnyUrl(f"email://account/{account}"),
                name=f"Gmail Account: {account}",
                description=f"Gmail account {account}",
                mimeType="application/json",
            )
        )
    
    # Add email resources
    for resource_id, email_resource in email_resources.items():
        resources.append(
            types.Resource(
                uri=AnyUrl(f"email://message/{resource_id}"),
                name=f"Email: {email_resource.subject}",
                description=f"Email from {email_resource.account} in {email_resource.mailbox}",
                mimeType="application/json",
            )
        )
    
    return resources

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str:
    """
    Read a specific email resource by its URI.
    """
    if uri.scheme != "email":
        raise ValueError(f"Unsupported URI scheme: {uri.scheme}")

    path = uri.path
    if not path:
        raise ValueError("Invalid email URI")
    
    path = path.lstrip("/")
    parts = path.split("/")
    
    if len(parts) < 2:
        raise ValueError("Invalid email URI format")
    
    resource_type = parts[0]
    resource_id = parts[1]
    
    if resource_type == "account":
        # Resource is an account
        account = resource_id
        if account not in auth_manager.list_authenticated_accounts():
            raise ValueError(f"Account not found: {account}")
        
        # Get account information
        if account not in email_clients:
            # Authenticate and create client
            creds = auth_manager.get_credentials(account)
            if not creds:
                raise ValueError(f"No valid credentials for account: {account}")
            
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        # Get mailboxes
        mailboxes = await client.list_mailboxes()
        
        # Get recent emails from inbox
        recent_emails = await client.get_recent_emails(limit=5)
        
        # Create resource content
        content = {
            "account": account,
            "mailboxes": mailboxes,
            "recent_emails": recent_emails
        }
        
        # Store email resources
        for email in recent_emails:
            resource_id = f"{account}_{email['mailbox']}_{email['id']}"
            email_resources[resource_id] = EmailResource(
                email_id=email['id'],
                mailbox=email['mailbox'],
                account=account,
                subject=email['subject']
            )
        
        # Notify clients that resources have changed
        await server.request_context.session.send_resource_list_changed()
        
        return json.dumps(content, indent=2)
    
    elif resource_type == "message":
        # Resource is an email message
        if resource_id not in email_resources:
            raise ValueError(f"Email not found: {resource_id}")
        
        email_resource = email_resources[resource_id]
        account = email_resource.account
        mailbox = email_resource.mailbox
        email_id = email_resource.email_id
        
        if account not in email_clients:
            # Authenticate and create client
            creds = auth_manager.get_credentials(account)
            if not creds:
                raise ValueError(f"No valid credentials for account: {account}")
            
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        # Get email details
        email_data = await client.get_email(email_id, mailbox)
        if not email_data:
            raise ValueError(f"Failed to retrieve email: {email_id}")
        
        return json.dumps(email_data, indent=2)
    
    else:
        raise ValueError(f"Unknown resource type: {resource_type}")

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """
    List available prompts.
    Each prompt can have optional arguments to customize its behavior.
    """
    return [
        types.Prompt(
            name="summarize-emails",
            description="Creates a summary of recent emails",
            arguments=[
                types.PromptArgument(
                    name="account",
                    description="Email account to summarize",
                    required=True,
                ),
                types.PromptArgument(
                    name="mailbox",
                    description="Mailbox to summarize (e.g., INBOX)",
                    required=False,
                ),
                types.PromptArgument(
                    name="count",
                    description="Number of emails to summarize",
                    required=False,
                )
            ],
        )
    ]

@server.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None
) -> types.GetPromptResult:
    """
    Generate a prompt by combining arguments with server state.
    """
    if name != "summarize-emails":
        raise ValueError(f"Unknown prompt: {name}")

    if not arguments or "account" not in arguments:
        raise ValueError("Missing required argument: account")
    
    account = arguments["account"]
    mailbox = arguments.get("mailbox", "INBOX")
    count = int(arguments.get("count", "5"))
    
    if account not in auth_manager.list_authenticated_accounts():
        raise ValueError(f"Account not found: {account}")
    
    # Get emails to summarize
    if account not in email_clients:
        # Authenticate and create client
        creds = auth_manager.get_credentials(account)
        if not creds:
            raise ValueError(f"No valid credentials for account: {account}")
        
        client = GmailImapClient(account, creds)
        await client.connect()
        email_clients[account] = client
    
    client = email_clients[account]
    
    # Get recent emails
    emails = await client.get_recent_emails(mailbox, count)
    
    # Create email summary text
    email_summaries = []
    for email in emails:
        email_summaries.append(
            f"From: {email['from']}\n"
            f"Subject: {email['subject']}\n"
            f"Date: {email['date']}\n"
            f"Content: {email['body'][:500]}...\n"
        )
    
    email_text = "\n\n---\n\n".join(email_summaries)
    
    return types.GetPromptResult(
        description=f"Summarize recent emails from {account} in {mailbox}",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"Please summarize the following {len(emails)} recent emails from my {mailbox} in {account}:\n\n{email_text}",
                ),
            )
        ],
    )

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="authenticate-gmail",
            description="Authenticate a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                },
                "required": ["email"],
            },
        ),
        types.Tool(
            name="search-emails",
            description="Search for emails in a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "mailbox": {"type": "string"},
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["account", "query"],
            },
        ),
        types.Tool(
            name="get-unread-emails",
            description="Get unread emails from a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "mailbox": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["account"],
            },
        ),
        types.Tool(
            name="send-email",
            description="Send an email from a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "cc": {"type": "string"},
                    "bcc": {"type": "string"},
                    "html_body": {"type": "string"},
                    "attachments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "filename": {"type": "string"},
                                "content_type": {"type": "string"}
                            },
                            "required": ["path"]
                        }
                    }
                },
                "required": ["account", "to", "subject", "body"],
            },
        ),
        types.Tool(
            name="create-label",
            description="Create a new label/mailbox in a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "label_name": {"type": "string"},
                },
                "required": ["account", "label_name"],
            },
        ),
        types.Tool(
            name="delete-label",
            description="Delete a label/mailbox from a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "label_name": {"type": "string"},
                },
                "required": ["account", "label_name"],
            },
        ),
        types.Tool(
            name="list-labels",
            description="List all labels/mailboxes in a Gmail account",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                },
                "required": ["account"],
            },
        ),
        types.Tool(
            name="move-email",
            description="Move an email from one label/mailbox to another",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "email_id": {"type": "string"},
                    "source_mailbox": {"type": "string"},
                    "target_mailbox": {"type": "string"},
                },
                "required": ["account", "email_id", "source_mailbox", "target_mailbox"],
            },
        ),
        types.Tool(
            name="download-attachment",
            description="Download an attachment from an email",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "email_id": {"type": "string"},
                    "attachment_index": {"type": "integer"},
                    "mailbox": {"type": "string"},
                    "download_dir": {"type": "string"},
                },
                "required": ["account", "email_id", "attachment_index"],
            },
        ),
        types.Tool(
            name="mark-as-read",
            description="Mark an email as read",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "email_id": {"type": "string"},
                    "mailbox": {"type": "string"},
                },
                "required": ["account", "email_id"],
            },
        ),
        types.Tool(
            name="mark-as-unread",
            description="Mark an email as unread",
            inputSchema={
                "type": "object",
                "properties": {
                    "account": {"type": "string"},
                    "email_id": {"type": "string"},
                    "mailbox": {"type": "string"},
                },
                "required": ["account", "email_id"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Tools can modify server state and notify clients of changes.
    """
    if not arguments:
        raise ValueError("Missing arguments")
    
    if name == "authenticate-gmail":
        email = arguments.get("email")
        if not email:
            raise ValueError("Missing email address")
        
        # Use home directory for credentials
        home_dir = str(Path.home())
        creds_dir = Path(os.path.join(home_dir, ".gmail_imap_mcp_credentials"))
        creds_dir.mkdir(exist_ok=True)
        
        # Check if client_secret.json exists
        client_secret_path = creds_dir / "client_secret.json"
        if not client_secret_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=(
                        "Client secret file not found. Please create a Google Cloud project, "
                        "enable the Gmail API, and download the OAuth client ID credentials.\n\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a new project or select an existing one\n"
                        "3. Enable the Gmail API\n"
                        "4. Create OAuth 2.0 credentials (Desktop app)\n"
                        "5. Download the client configuration file\n"
                        "6. Save it as '.gmail_imap_mcp_credentials/client_secret.json'\n"
                    ),
                )
            ]
        
        try:
            # Authenticate the account
            creds = auth_manager.authenticate(email)
            
            # Create and test client connection
            client = GmailImapClient(email, creds)
            await client.connect()
            
            # Store client for future use
            email_clients[email] = client
            
            # Get mailboxes to verify connection
            mailboxes = await client.list_mailboxes()
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully authenticated Gmail account: {email}\n\nAvailable mailboxes: {', '.join(mailboxes[:10])}",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Failed to authenticate Gmail account: {str(e)}",
                )
            ]
    
    elif name == "search-emails":
        account = arguments.get("account")
        mailbox = arguments.get("mailbox", "INBOX")
        query = arguments.get("query")
        limit = int(arguments.get("limit", 10))
        
        if not account or not query:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        # Convert query to IMAP search criteria
        search_criteria = "ALL"
        if query.lower() != "all":
            # Simple conversion of common search terms
            if "from:" in query.lower():
                match = re.search(r'from:\s*"?([^"]+)"?', query, re.IGNORECASE)
                if match:
                    search_criteria = f'FROM "{match.group(1)}"'
            elif "subject:" in query.lower():
                match = re.search(r'subject:\s*"?([^"]+)"?', query, re.IGNORECASE)
                if match:
                    search_criteria = f'SUBJECT "{match.group(1)}"'
            else:
                # Basic text search
                search_criteria = f'TEXT "{query}"'
        
        try:
            # Search for emails
            emails = await client.search_emails(search_criteria, mailbox, limit)
            
            # Store email resources
            for email in emails:
                resource_id = f"{account}_{email['mailbox']}_{email['id']}"
                email_resources[resource_id] = EmailResource(
                    email_id=email['id'],
                    mailbox=email['mailbox'],
                    account=account,
                    subject=email['subject']
                )
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            # Format results
            if emails:
                email_list = "\n\n".join([
                    f"From: {email['from']}\n"
                    f"Subject: {email['subject']}\n"
                    f"Date: {email['date']}\n"
                    f"Resource URI: email://message/{account}_{email['mailbox']}_{email['id']}"
                    for email in emails
                ])
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Found {len(emails)} emails matching query '{query}' in {mailbox}:\n\n{email_list}",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"No emails found matching query '{query}' in {mailbox}.",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error searching emails: {str(e)}",
                )
            ]
    
    elif name == "get-unread-emails":
        account = arguments.get("account")
        mailbox = arguments.get("mailbox", "INBOX")
        limit = int(arguments.get("limit", 10))
        
        if not account:
            raise ValueError("Missing required argument: account")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Get unread emails
            emails = await client.get_unread_emails(mailbox, limit)
            
            # Store email resources
            for email in emails:
                resource_id = f"{account}_{email['mailbox']}_{email['id']}"
                email_resources[resource_id] = EmailResource(
                    email_id=email['id'],
                    mailbox=email['mailbox'],
                    account=account,
                    subject=email['subject']
                )
            
            # Notify clients that resources have changed
            await server.request_context.session.send_resource_list_changed()
            
            # Format results
            if emails:
                email_list = "\n\n".join([
                    f"From: {email['from']}\n"
                    f"Subject: {email['subject']}\n"
                    f"Date: {email['date']}\n"
                    f"Resource URI: email://message/{account}_{email['mailbox']}_{email['id']}"
                    for email in emails
                ])
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Found {len(emails)} unread emails in {mailbox}:\n\n{email_list}",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"No unread emails found in {mailbox}.",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error getting unread emails: {str(e)}",
                )
            ]
    
    elif name == "send-email":
        account = arguments.get("account")
        to = arguments.get("to")
        subject = arguments.get("subject")
        body = arguments.get("body")
        cc = arguments.get("cc")
        bcc = arguments.get("bcc")
        html_body = arguments.get("html_body")
        attachments = arguments.get("attachments", [])
        
        if not account or not to or not subject or not body:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Send email
            success = await client.send_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                html_body=html_body,
                attachments=attachments
            )
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Email sent successfully to {to}",
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error sending email: {str(e)}",
                )
            ]
    
    elif name == "create-label":
        account = arguments.get("account")
        label_name = arguments.get("label_name")
        
        if not account or not label_name:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Create label
            success = await client.create_label(label_name)
            
            if success:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Label '{label_name}' created successfully",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to create label '{label_name}'",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error creating label: {str(e)}",
                )
            ]
    
    elif name == "delete-label":
        account = arguments.get("account")
        label_name = arguments.get("label_name")
        
        if not account or not label_name:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Delete label
            success = await client.delete_label(label_name)
            
            if success:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Label '{label_name}' deleted successfully",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to delete label '{label_name}'",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error deleting label: {str(e)}",
                )
            ]
    
    elif name == "list-labels":
        account = arguments.get("account")
        
        if not account:
            raise ValueError("Missing required argument: account")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # List labels
            labels = await client.list_mailboxes()
            
            if labels:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Labels for {account}:\n\n{', '.join(labels)}",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"No labels found for {account}",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error listing labels: {str(e)}",
                )
            ]
    
    elif name == "move-email":
        account = arguments.get("account")
        email_id = arguments.get("email_id")
        source_mailbox = arguments.get("source_mailbox")
        target_mailbox = arguments.get("target_mailbox")
        
        if not account or not email_id or not source_mailbox or not target_mailbox:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Extract the actual email ID from the resource URI
            if email_id.startswith("email://message/"):
                parts = email_id.split("_")
                if len(parts) >= 3:
                    # The last part should be the actual email ID
                    actual_email_id = parts[-1]
                    success = await client.move_email(actual_email_id, source_mailbox, target_mailbox)
                else:
                    success = False
            else:
                success = await client.move_email(email_id, source_mailbox, target_mailbox)
            
            if success:
                # Update email resources if needed
                resource_id = f"{account}_{source_mailbox}_{email_id}"
                if resource_id in email_resources:
                    # Update the resource with new mailbox
                    new_resource_id = f"{account}_{target_mailbox}_{email_id}"
                    email_resource = email_resources.pop(resource_id)
                    email_resource.mailbox = target_mailbox
                    email_resources[new_resource_id] = email_resource
                    
                    # Notify clients that resources have changed
                    await server.request_context.session.send_resource_list_changed()
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"Email moved successfully from '{source_mailbox}' to '{target_mailbox}'",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to move email from '{source_mailbox}' to '{target_mailbox}'",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error moving email: {str(e)}",
                )
            ]
    
    elif name == "download-attachment":
        account = arguments.get("account")
        email_id = arguments.get("email_id")
        attachment_index = arguments.get("attachment_index")
        mailbox = arguments.get("mailbox", "INBOX")
        download_dir = arguments.get("download_dir", "downloads")
        
        if not account or not email_id or attachment_index is None:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Download attachment
            file_path = await client.download_attachment(
                email_id=email_id,
                attachment_index=attachment_index,
                mailbox=mailbox,
                download_dir=download_dir
            )
            
            if file_path:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Attachment downloaded successfully to {file_path}",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to download attachment. Attachment may not exist or index is invalid.",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error downloading attachment: {str(e)}",
                )
            ]
    
    elif name == "mark-as-read":
        account = arguments.get("account")
        email_id = arguments.get("email_id")
        mailbox = arguments.get("mailbox", "INBOX")
        
        if not account or not email_id:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Mark as read
            # Extract the actual email ID from the resource URI
            if email_id.startswith("email://message/"):
                parts = email_id.split("_")
                if len(parts) >= 3:
                    # The last part should be the actual email ID
                    actual_email_id = parts[-1]
                    success = await client.mark_as_read(actual_email_id, mailbox)
                else:
                    success = False
            else:
                success = await client.mark_as_read(email_id, mailbox)
            
            if success:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Email marked as read successfully",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to mark email as read",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error marking email as read: {str(e)}",
                )
            ]
    
    elif name == "mark-as-unread":
        account = arguments.get("account")
        email_id = arguments.get("email_id")
        mailbox = arguments.get("mailbox", "INBOX")
        
        if not account or not email_id:
            raise ValueError("Missing required arguments")
        
        if account not in auth_manager.list_authenticated_accounts():
            return [
                types.TextContent(
                    type="text",
                    text=f"Account not authenticated: {account}. Please authenticate first.",
                )
            ]
        
        # Get or create client
        if account not in email_clients:
            creds = auth_manager.get_credentials(account)
            client = GmailImapClient(account, creds)
            await client.connect()
            email_clients[account] = client
        
        client = email_clients[account]
        
        try:
            # Mark as unread
            success = await client.mark_as_unread(email_id, mailbox)
            
            if success:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Email marked as unread successfully",
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Failed to mark email as unread",
                    )
                ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error marking email as unread: {str(e)}",
                )
            ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="gmail-imap-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )