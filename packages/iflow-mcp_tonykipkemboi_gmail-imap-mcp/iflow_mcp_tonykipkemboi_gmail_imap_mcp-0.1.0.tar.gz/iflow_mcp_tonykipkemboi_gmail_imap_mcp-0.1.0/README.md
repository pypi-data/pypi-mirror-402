# Gmail IMAP MCP Server

A Model Context Protocol (MCP) server for Gmail integration using IMAP. This server allows AI assistants to interact with Gmail accounts, providing functionality to read, search, and manage emails.

## Features

- OAuth2 authentication with Gmail
- Read emails from Gmail accounts
- Search emails with advanced query options
- View unread emails
- Send emails with attachments
- Manage labels (create, delete, list)
- Move emails between labels
- Download attachments
- Mark emails as read/unread
- Support for multiple Gmail accounts
- Integration with AI assistants through MCP

## Prerequisites

Before running the Gmail IMAP MCP server, ensure you have the following:

1. Python 3.12 or higher
2. Google Cloud Project with Gmail API enabled
3. OAuth 2.0 Client ID credentials

## Installation

### Install from source

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gmail-imap-mcp.git
   cd gmail-imap-mcp
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows
   .venv\Scripts\activate
   # On Unix/MacOS
   source .venv/bin/activate
   ```

3. Install the package:
   ```
   pip install -e .
   ```

## Setup Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the client configuration file
5. Save the downloaded file as `client_secret.json` in the credentials directory:
   ```
   mkdir -p ~/.gmail_imap_mcp_credentials
   # Move the downloaded file to ~/.gmail_imap_mcp_credentials/client_secret.json
   ```

## Architecture and Implementation Details

### Credential Storage

The Gmail IMAP MCP server stores OAuth2 credentials in the user's home directory at `~/.gmail_imap_mcp_credentials/`. This approach offers several advantages:

1. **Security**: Credentials are stored in a user-specific location rather than in the application directory
2. **Persistence**: Credentials persist across different sessions and application restarts
3. **Compatibility**: Avoids permission issues on read-only file systems

The credentials directory contains:
- `client_secret.json`: Your OAuth client credentials from Google Cloud Console
- Token files for each authenticated Gmail account (format: `token_{email_address}.json`)

### IMAP Implementation

The server uses Python's `imaplib2` library for IMAP operations with Gmail. Key implementation details include:

1. **Connection**: Secure connection to Gmail's IMAP server (`imap.gmail.com`) on port 993
2. **Authentication**: OAuth2 authentication using XOAUTH2 mechanism
3. **Email Retrieval**: Emails are retrieved using RFC822 format and parsed with Python's `email` module
4. **Label Management**: Gmail labels are managed through IMAP mailbox operations

### Email ID Format

Email IDs in the system follow this format:
```
email://message/{account}_{mailbox}_{id}
```

Where:
- `{account}`: The Gmail account address
- `{mailbox}`: The mailbox/label containing the email
- `{id}`: The unique IMAP ID of the email

This format allows the system to uniquely identify emails across different accounts and mailboxes.

## Usage

### Starting the Server

Run the Gmail IMAP MCP server:

```
gmail-imap-mcp
```

### Authenticating Gmail Accounts

1. Use the `authenticate-gmail` tool with your email address
2. Follow the OAuth2 authentication flow in your browser
3. Once authenticated, the server will store your credentials for future use

## Available Tools and Examples

The Gmail IMAP MCP server provides a comprehensive set of tools for interacting with Gmail accounts. Below is a detailed list of all available tools along with examples of how to use them.

### Authentication

#### 1. authenticate-gmail
Authenticate a Gmail account to use with the MCP server.

**Parameters:**
- `email`: Email address to authenticate

**Example:**
```json
{
  "name": "authenticate-gmail",
  "arguments": {
    "email": "your.email@gmail.com"
  }
}
```

### Email Retrieval and Search

#### 2. search-emails
Search for emails in a Gmail account using various search criteria.

**Parameters:**
- `account`: Email account to search in
- `mailbox`: Mailbox to search in (default: INBOX)
- `query`: Search query
- `limit`: Maximum number of emails to return (default: 10)

**Example - Search for emails from a specific sender:**
```json
{
  "name": "search-emails",
  "arguments": {
    "account": "your.email@gmail.com",
    "mailbox": "INBOX",
    "query": "from:sender@example.com",
    "limit": 5
  }
}
```

**Example - Search for emails with a specific subject:**
```json
{
  "name": "search-emails",
  "arguments": {
    "account": "your.email@gmail.com",
    "query": "subject:\"Meeting Invitation\""
  }
}
```

**Example - Search for emails with specific text in the body:**
```json
{
  "name": "search-emails",
  "arguments": {
    "account": "your.email@gmail.com",
    "query": "TEXT \"project update\""
  }
}
```

#### 3. get-unread-emails
Get unread emails from a Gmail account.

**Parameters:**
- `account`: Email account to get emails from
- `mailbox`: Mailbox to get emails from (default: INBOX)
- `limit`: Maximum number of emails to return (default: 10)

**Example:**
```json
{
  "name": "get-unread-emails",
  "arguments": {
    "account": "your.email@gmail.com",
    "limit": 20
  }
}
```

### Email Composition and Sending

#### 4. send-email
Send an email from a Gmail account with optional attachments and HTML content.

**Parameters:**
- `account`: Email account to send from
- `to`: Recipient email address(es), comma-separated for multiple
- `subject`: Email subject
- `body`: Plain text email body
- `cc`: Carbon copy recipients (optional)
- `bcc`: Blind carbon copy recipients (optional)
- `html_body`: HTML version of the email body (optional)
- `attachments`: List of attachment objects (optional)
  - Each attachment object requires:
    - `path`: Path to the file
    - `filename`: Custom filename (optional)
    - `content_type`: MIME type (optional)

**Example - Simple email:**
```json
{
  "name": "send-email",
  "arguments": {
    "account": "your.email@gmail.com",
    "to": "recipient@example.com",
    "subject": "Hello from Gmail MCP",
    "body": "This is a test email sent via the Gmail IMAP MCP server."
  }
}
```

**Example - Email with CC, BCC, and HTML content:**
```json
{
  "name": "send-email",
  "arguments": {
    "account": "your.email@gmail.com",
    "to": "recipient@example.com",
    "subject": "Meeting Agenda",
    "body": "Please find the agenda for our upcoming meeting.",
    "cc": "manager@example.com",
    "bcc": "archive@example.com",
    "html_body": "<h1>Meeting Agenda</h1><p>Please find the agenda for our <b>upcoming meeting</b>.</p>"
  }
}
```

**Example - Email with attachment:**
```json
{
  "name": "send-email",
  "arguments": {
    "account": "your.email@gmail.com",
    "to": "recipient@example.com",
    "subject": "Document Attached",
    "body": "Please find the attached document.",
    "attachments": [
      {
        "path": "/path/to/document.pdf",
        "filename": "important_document.pdf",
        "content_type": "application/pdf"
      }
    ]
  }
}
```

### Label Management

#### 5. create-label
Create a new label/mailbox in a Gmail account.

**Parameters:**
- `account`: Email account to create label in
- `label_name`: Name of the label to create

**Example:**
```json
{
  "name": "create-label",
  "arguments": {
    "account": "your.email@gmail.com",
    "label_name": "ProjectX"
  }
}
```

#### 6. delete-label
Delete a label/mailbox from a Gmail account.

**Parameters:**
- `account`: Email account to delete label from
- `label_name`: Name of the label to delete

**Example:**
```json
{
  "name": "delete-label",
  "arguments": {
    "account": "your.email@gmail.com",
    "label_name": "OldProject"
  }
}
```

#### 7. list-labels
List all labels/mailboxes in a Gmail account.

**Parameters:**
- `account`: Email account to list labels from

**Example:**
```json
{
  "name": "list-labels",
  "arguments": {
    "account": "your.email@gmail.com"
  }
}
```

### Email Organization

#### 8. move-email
Move an email from one label/mailbox to another.

**Parameters:**
- `account`: Email account
- `email_id`: Email ID to move (format: `email://message/{account}_{mailbox}_{id}`)
- `source_mailbox`: Source mailbox
- `target_mailbox`: Target mailbox

**Example:**
```json
{
  "name": "move-email",
  "arguments": {
    "account": "your.email@gmail.com",
    "email_id": "email://message/your.email@gmail.com_INBOX_12345",
    "source_mailbox": "INBOX",
    "target_mailbox": "ProjectX"
  }
}
```

### Attachment Handling

#### 9. download-attachment
Download an attachment from an email.

**Parameters:**
- `account`: Email account
- `email_id`: Email ID (format: `email://message/{account}_{mailbox}_{id}`)
- `attachment_index`: Index of the attachment to download (0-based)
- `mailbox`: Mailbox containing the email (default: INBOX)
- `download_dir`: Directory to save the attachment to (default: "downloads")

**Example:**
```json
{
  "name": "download-attachment",
  "arguments": {
    "account": "your.email@gmail.com",
    "email_id": "email://message/your.email@gmail.com_INBOX_12345",
    "attachment_index": 0,
    "download_dir": "my_attachments"
  }
}
```

### Email Status Management

#### 10. mark-as-read
Mark an email as read.

**Parameters:**
- `account`: Email account
- `email_id`: Email ID (format: `email://message/{account}_{mailbox}_{id}`)
- `mailbox`: Mailbox containing the email (default: INBOX)

**Example:**
```json
{
  "name": "mark-as-read",
  "arguments": {
    "account": "your.email@gmail.com",
    "email_id": "email://message/your.email@gmail.com_INBOX_12345"
  }
}
```

#### 11. mark-as-unread
Mark an email as unread.

**Parameters:**
- `account`: Email account
- `email_id`: Email ID (format: `email://message/{account}_{mailbox}_{id}`)
- `mailbox`: Mailbox containing the email (default: INBOX)

**Example:**
```json
{
  "name": "mark-as-unread",
  "arguments": {
    "account": "your.email@gmail.com",
    "email_id": "email://message/your.email@gmail.com_INBOX_12345"
  }
}
```

## Available Prompts

The server provides the following prompts for AI assistants to use:

### 1. summarize-emails
Creates a summary of recent emails.

**Parameters:**
- `account`: Email account to summarize
- `mailbox`: Mailbox to summarize (default: INBOX)
- `count`: Number of emails to summarize (default: 5)

**Example:**
```json
{
  "name": "summarize-emails",
  "arguments": {
    "account": "your.email@gmail.com",
    "mailbox": "INBOX",
    "count": 10
  }
}
```

## Integration with AI Assistants

The Gmail IMAP MCP server can be integrated with AI assistants that support the Model Context Protocol (MCP). Here's a typical workflow:

1. **Authentication**: The AI assistant uses the `authenticate-gmail` tool to authenticate the user's Gmail account.

2. **Email Management**: The assistant can retrieve, search, and manage emails using the various tools provided by the server.

3. **Email Composition**: The assistant can help draft and send emails based on user instructions.

4. **Email Organization**: The assistant can help organize emails by creating labels, moving emails between labels, and marking emails as read/unread.

5. **Email Summarization**: The assistant can summarize emails using the `summarize-emails` prompt.

## Connecting with AI Assistants

### Claude Desktop

To connect the Gmail IMAP MCP server with Claude Desktop:

1. Start the Gmail IMAP MCP server:
   ```bash
   python -m gmail_imap_mcp.server
   ```

2. Open Claude Desktop and navigate to Settings (gear icon)

3. Scroll down to the "Advanced" section and click on "Edit MCP Configuration"

4. Add the Gmail IMAP MCP server configuration:
   ```json
   {
     "servers": [
       {
         "name": "Gmail IMAP",
         "url": "http://localhost:8080",
         "tools": [
           "list-emails",
           "get-email",
           "search-emails",
           "send-email",
           "list-mailboxes",
           "create-label",
           "move-email",
           "mark-as-read",
           "download-attachment"
         ]
       }
     ]
   }
   ```

5. Click "Save" and restart Claude Desktop

6. You can now ask Claude to interact with your Gmail account, for example:
   - "Show me my unread emails"
   - "Send an email to [recipient] about [subject]"
   - "Create a new label called 'Important'"
   - "Move the email from [sender] to the 'Important' label"

### Windsurf IDE

To connect the Gmail IMAP MCP server with Windsurf IDE:

1. Start the Gmail IMAP MCP server:
   ```bash
   python -m gmail_imap_mcp.server
   ```

2. Open Windsurf IDE and navigate to Settings

3. Find the "AI Flow" or "MCP Configuration" section

4. Add the Gmail IMAP MCP server configuration:
   ```json
   {
     "servers": [
       {
         "name": "Gmail IMAP",
         "url": "http://localhost:8080",
         "tools": [
           "list-emails",
           "get-email",
           "search-emails",
           "send-email",
           "list-mailboxes",
           "create-label",
           "move-email",
           "mark-as-read",
           "download-attachment"
         ]
       }
     ]
   }
   ```

5. Save the settings and restart Windsurf if necessary

6. You can now ask Cascade (Windsurf's AI assistant) to interact with your Gmail account using the same commands as with Claude Desktop

## Common Use Cases

### 1. Email Triage
```
Assistant: I'll help you triage your unread emails.
User: Yes, please check my unread emails.
Assistant: [Uses get-unread-emails tool]
Assistant: You have 5 unread emails. The most urgent appears to be from your boss about the quarterly report due tomorrow.
User: Mark that as read and I'll look at it right away.
Assistant: [Uses mark-as-read tool]
```

### 2. Email Search and Organization
```
Assistant: Would you like me to find specific emails for you?
User: Yes, find all emails from john@example.com about the project budget.
Assistant: [Uses search-emails tool with query "from:john@example.com project budget"]
Assistant: I found 3 emails from John about the project budget. Would you like me to create a label for these?
User: Yes, create a "Budget" label and move them there.
Assistant: [Uses create-label tool followed by move-email tool for each email]
```

### 3. Email Composition
```
Assistant: Would you like me to draft an email for you?
User: Yes, write a follow-up email to the marketing team about our campaign results.
Assistant: [Drafts email content]
Assistant: Here's a draft. Would you like me to send it?
User: Yes, but add Sarah in CC.
Assistant: [Uses send-email tool with the drafted content and CC]
```

## Gmail-Specific Considerations

### Label Naming Conventions

Gmail has specific requirements for label names:

1. Label names are case-sensitive
2. Some special characters may not be allowed
3. System labels (like INBOX, Sent, Trash) cannot be created or deleted
4. Nested labels are represented with a forward slash (e.g., "Projects/ProjectX")

### Email ID Format

The email ID format used by this MCP server is:
```
email://message/{account}_{mailbox}_{id}
```

When using tools that require an email ID (like `mark-as-read` or `move-email`), make sure to use the complete resource URI returned by email retrieval tools.

## Security Considerations

- The server stores OAuth2 credentials locally in the `~/.gmail_imap_mcp_credentials` directory
- Never share your `client_secret.json` or token files
- The server only connects to Gmail's IMAP server using secure connections
- Email attachments are downloaded to the `downloads` directory by default
- Be cautious when using the server in shared environments to protect email data

## Troubleshooting

### Authentication Issues
- Ensure your `client_secret.json` is correctly placed in the `~/.gmail_imap_mcp_credentials` directory
- Check that you've enabled the Gmail API in your Google Cloud Project
- Try re-authenticating if your token has expired
- If you see "Read-only file system" errors, ensure the credentials directory is writable

### Connection Issues
- Verify your internet connection
- Ensure that your Google account doesn't have any security restrictions that might block IMAP access
- Check if you need to enable "Less secure app access" in your Google account settings

### Email Sending Issues
- Verify that your Gmail account allows SMTP access
- Check if you need to enable "Less secure app access" in your Google account settings
- Ensure attachments are not too large (Gmail has a 25MB limit)

### Label Management Issues
- If creating labels fails, check if the label already exists (case-sensitive)
- System labels cannot be created or deleted
- Ensure label names follow Gmail's naming conventions

### Email Movement Issues
- If moving emails between labels fails, ensure both source and target labels exist
- Check that the email ID format is correct
- Verify that you have sufficient permissions to modify the email

### Email ID Parsing Issues
- If operations on email IDs fail, ensure you're using the complete resource URI
- The system parses the last part of the URI as the actual email ID
- Format should be: `email://message/{account}_{mailbox}_{id}`

## License

[MIT License](LICENSE)

## Support

For issues and feature requests, please open an issue on the GitHub repository.