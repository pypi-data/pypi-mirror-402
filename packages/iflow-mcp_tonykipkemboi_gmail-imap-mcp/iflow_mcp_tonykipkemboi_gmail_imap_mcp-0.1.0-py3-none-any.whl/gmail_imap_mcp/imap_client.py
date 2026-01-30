"""
Gmail IMAP client module for the MCP server.
Handles IMAP operations with Gmail.
"""
import imaplib
import email
import base64
import re
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.header import decode_header
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from google.oauth2.credentials import Credentials


class GmailImapClient:
    """Client for interacting with Gmail via IMAP."""
    
    def __init__(self, email_address: str, credentials: Credentials):
        """
        Initialize the Gmail IMAP client.
        
        Args:
            email_address: Gmail address to connect to
            credentials: OAuth2 credentials
        """
        self.email_address = email_address
        self.credentials = credentials
        self.imap = None
    
    async def connect(self) -> None:
        """
        Connect to Gmail's IMAP server using OAuth2.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Connect to Gmail's IMAP server
            self.imap = imaplib.IMAP4_SSL('imap.gmail.com')
            
            # Authenticate with OAuth2
            auth_string = f'user={self.email_address}\1auth=Bearer {self.credentials.token}\1\1'
            self.imap.authenticate('XOAUTH2', lambda x: auth_string)
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Gmail IMAP: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from the IMAP server."""
        if self.imap:
            try:
                self.imap.logout()
            except:
                pass
            self.imap = None
    
    async def list_mailboxes(self) -> List[str]:
        """
        List all available mailboxes/labels.
        
        Returns:
            List of mailbox/label names
        """
        if not self.imap:
            await self.connect()
        
        try:
            # List all mailboxes
            result, mailboxes = self.imap.list()
            
            if result != 'OK':
                return []
            
            # Parse mailbox names
            mailbox_list = []
            for mailbox in mailboxes:
                if not mailbox:
                    continue
                
                # Parse mailbox name
                try:
                    # Mailbox format is typically: (flags) "separator" "name"
                    parts = mailbox.decode().split(' "')
                    if len(parts) >= 2:
                        # Extract the name part and remove the trailing quote
                        name = parts[-1].rstrip('"')
                        mailbox_list.append(name)
                except Exception as e:
                    print(f"Error parsing mailbox: {str(e)}")
            
            return mailbox_list
        except Exception as e:
            print(f"Error listing mailboxes: {str(e)}")
            return []
    
    async def select_mailbox(self, mailbox: str = 'INBOX') -> int:
        """
        Select a mailbox/label to work with.
        
        Args:
            mailbox: Mailbox name to select
            
        Returns:
            Number of messages in the mailbox
            
        Raises:
            ValueError: If mailbox selection fails
        """
        if not self.imap:
            await self.connect()
        
        result, data = self.imap.select(mailbox)
        
        if result != 'OK':
            raise ValueError(f"Failed to select mailbox {mailbox}: {data}")
        
        return int(data[0])
    
    def _decode_email_subject(self, msg: email.message.Message) -> str:
        """
        Decode email subject.
        
        Args:
            msg: Email message
            
        Returns:
            Decoded subject
        """
        subject = msg.get('Subject', '')
        decoded_chunks = []
        
        for chunk, encoding in decode_header(subject):
            if isinstance(chunk, bytes):
                if encoding:
                    try:
                        decoded_chunks.append(chunk.decode(encoding))
                    except:
                        decoded_chunks.append(chunk.decode('utf-8', errors='replace'))
                else:
                    decoded_chunks.append(chunk.decode('utf-8', errors='replace'))
            else:
                decoded_chunks.append(chunk)
        
        return ''.join(decoded_chunks)
    
    def _extract_email_content(self, msg: email.message.Message) -> Tuple[str, List[Dict]]:
        """
        Extract email content and attachments.
        
        Args:
            msg: Email message
            
        Returns:
            Tuple of (email_body, attachments)
        """
        body = ""
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip multipart containers
                if content_type == "multipart/alternative":
                    continue
                
                # Handle attachments
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        # Decode filename if needed
                        if isinstance(filename, bytes):
                            filename = filename.decode()
                        
                        payload = part.get_payload(decode=True)
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(payload),
                            "data": base64.b64encode(payload).decode('utf-8')
                        })
                # Handle email body
                elif content_type in ["text/plain", "text/html"]:
                    try:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or 'utf-8'
                            try:
                                decoded_payload = payload.decode(charset)
                            except:
                                decoded_payload = payload.decode('utf-8', errors='replace')
                            
                            # Prefer HTML content if both are available
                            if content_type == "text/html" or not body:
                                body = decoded_payload
                    except:
                        pass
        else:
            # Handle non-multipart messages
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                try:
                    body = payload.decode(charset)
                except:
                    body = payload.decode('utf-8', errors='replace')
        
        return body, attachments
    
    async def search_emails(self, criteria: str, mailbox: str = 'INBOX', limit: int = 10) -> List[Dict]:
        """
        Search for emails using IMAP search criteria.
        
        Args:
            criteria: IMAP search criteria
            mailbox: Mailbox to search in
            limit: Maximum number of emails to return
            
        Returns:
            List of email data dictionaries
        """
        await self.select_mailbox(mailbox)
        
        result, data = self.imap.search(None, criteria)
        
        if result != 'OK':
            return []
        
        email_ids = data[0].split()
        
        # Get the most recent emails first (up to limit)
        email_ids = email_ids[-limit:] if limit < len(email_ids) else email_ids
        
        emails = []
        for email_id in reversed(email_ids):
            result, data = self.imap.fetch(email_id, '(RFC822)')
            
            if result != 'OK':
                continue
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract email data
            subject = self._decode_email_subject(msg)
            from_addr = msg.get('From', '')
            to_addr = msg.get('To', '')
            date_str = msg.get('Date', '')
            
            # Parse date
            try:
                date_tuple = email.utils.parsedate_tz(date_str)
                if date_tuple:
                    date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date_formatted = date_str
            except:
                date_formatted = date_str
            
            # Extract body and attachments
            body, attachments = self._extract_email_content(msg)
            
            emails.append({
                'id': email_id.decode(),
                'subject': subject,
                'from': from_addr,
                'to': to_addr,
                'date': date_formatted,
                'body': body,
                'attachments': attachments,
                'mailbox': mailbox
            })
        
        return emails
    
    async def get_email(self, email_id: str, mailbox: str = 'INBOX') -> Optional[Dict]:
        """
        Get a specific email by ID.
        
        Args:
            email_id: Email ID
            mailbox: Mailbox containing the email
            
        Returns:
            Email data dictionary or None if not found
        """
        await self.select_mailbox(mailbox)
        
        result, data = self.imap.fetch(email_id.encode(), '(RFC822)')
        
        if result != 'OK' or not data or data[0] is None:
            return None
        
        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Extract email data
        subject = self._decode_email_subject(msg)
        from_addr = msg.get('From', '')
        to_addr = msg.get('To', '')
        date_str = msg.get('Date', '')
        
        # Parse date
        try:
            date_tuple = email.utils.parsedate_tz(date_str)
            if date_tuple:
                date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                date_formatted = date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_formatted = date_str
        except:
            date_formatted = date_str
        
        # Extract body and attachments
        body, attachments = self._extract_email_content(msg)
        
        return {
            'id': email_id,
            'subject': subject,
            'from': from_addr,
            'to': to_addr,
            'date': date_formatted,
            'body': body,
            'attachments': attachments,
            'mailbox': mailbox
        }
    
    async def get_recent_emails(self, mailbox: str = 'INBOX', limit: int = 10) -> List[Dict]:
        """
        Get recent emails from a mailbox.
        
        Args:
            mailbox: Mailbox to get emails from
            limit: Maximum number of emails to return
            
        Returns:
            List of email data dictionaries
        """
        return await self.search_emails('ALL', mailbox, limit)
    
    async def get_unread_emails(self, mailbox: str = 'INBOX', limit: int = 10) -> List[Dict]:
        """
        Get unread emails from a mailbox.
        
        Args:
            mailbox: Mailbox to get emails from
            limit: Maximum number of emails to return
            
        Returns:
            List of email data dictionaries
        """
        return await self.search_emails('UNSEEN', mailbox, limit)
    
    async def send_email(self, to: str, subject: str, body: str, 
                        cc: Optional[str] = None, bcc: Optional[str] = None, 
                        html_body: Optional[str] = None,
                        attachments: Optional[List[Dict]] = None) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to: Recipient email address(es), comma-separated for multiple
            subject: Email subject
            body: Plain text email body
            cc: Carbon copy recipients, comma-separated for multiple
            bcc: Blind carbon copy recipients, comma-separated for multiple
            html_body: HTML version of the email body
            attachments: List of attachment dictionaries with keys:
                - path: Path to file (str)
                - filename: Optional custom filename (str)
                - content_type: Optional MIME type (str)
            
        Returns:
            True if email was sent successfully, False otherwise
            
        Raises:
            ValueError: If sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_address
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            if bcc:
                msg['Bcc'] = bcc
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments if any
            if attachments:
                # Convert to multipart/mixed if we have attachments
                mixed_msg = MIMEMultipart('mixed')
                # Copy headers
                for key, value in msg.items():
                    mixed_msg[key] = value
                
                # Attach the body
                mixed_msg.attach(msg)
                msg = mixed_msg
                
                for attachment in attachments:
                    path = attachment.get('path')
                    if not path:
                        continue
                    
                    filename = attachment.get('filename') or os.path.basename(path)
                    content_type = attachment.get('content_type')
                    
                    with open(path, 'rb') as f:
                        part = MIMEApplication(f.read())
                    
                    part.add_header('Content-Disposition', 'attachment', filename=filename)
                    if content_type:
                        part.set_type(content_type)
                    
                    msg.attach(part)
            
            # Connect to SMTP server
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                # Use OAuth2 for authentication
                auth_string = f'user={self.email_address}\1auth=Bearer {self.credentials.token}\1\1'
                smtp.ehlo()
                smtp.docmd('AUTH', 'XOAUTH2 ' + base64.b64encode(auth_string.encode()).decode())
                
                # Get all recipients
                all_recipients = []
                if to:
                    all_recipients.extend([addr.strip() for addr in to.split(',')])
                if cc:
                    all_recipients.extend([addr.strip() for addr in cc.split(',')])
                if bcc:
                    all_recipients.extend([addr.strip() for addr in bcc.split(',')])
                
                # Send email
                smtp.send_message(msg, from_addr=self.email_address, to_addrs=all_recipients)
                
            return True
        
        except Exception as e:
            raise ValueError(f"Failed to send email: {str(e)}")
    
    async def create_label(self, label_name: str) -> bool:
        """
        Create a new label/mailbox.
        
        Args:
            label_name: Name of the label to create
            
        Returns:
            True if label was created successfully, False otherwise
        """
        if not self.imap:
            await self.connect()
        
        try:
            result, data = self.imap.create(label_name)
            return result == 'OK'
        except Exception as e:
            return False
    
    async def delete_label(self, label_name: str) -> bool:
        """
        Delete a label/mailbox.
        
        Args:
            label_name: Name of the label to delete
            
        Returns:
            True if label was deleted successfully, False otherwise
        """
        if not self.imap:
            await self.connect()
        
        try:
            result, data = self.imap.delete(label_name)
            return result == 'OK'
        except Exception as e:
            return False
    
    async def move_email(self, email_id: str, source_mailbox: str, target_mailbox: str) -> bool:
        """
        Move an email from one mailbox to another.
        
        Args:
            email_id: Email ID to move
            source_mailbox: Source mailbox
            target_mailbox: Target mailbox
            
        Returns:
            True if email was moved successfully, False otherwise
        """
        if not self.imap:
            await self.connect()
        
        try:
            # Select source mailbox
            await self.select_mailbox(source_mailbox)
            
            # Copy email to target mailbox
            result, data = self.imap.copy(email_id.encode(), target_mailbox)
            if result != 'OK':
                return False
            
            # Mark the original email as deleted
            result, data = self.imap.store(email_id.encode(), '+FLAGS', '\\Deleted')
            if result != 'OK':
                return False
            
            # Expunge to actually delete
            self.imap.expunge()
            
            return True
        except Exception as e:
            return False
    
    async def download_attachment(self, email_id: str, attachment_index: int, 
                                 mailbox: str = 'INBOX', 
                                 download_dir: str = 'downloads') -> Optional[str]:
        """
        Download an email attachment.
        
        Args:
            email_id: Email ID
            attachment_index: Index of the attachment to download (0-based)
            mailbox: Mailbox containing the email
            download_dir: Directory to save the attachment to
            
        Returns:
            Path to the downloaded file or None if download failed
        """
        # Get the email
        email_data = await self.get_email(email_id, mailbox)
        if not email_data or 'attachments' not in email_data:
            return None
        
        attachments = email_data['attachments']
        if attachment_index < 0 or attachment_index >= len(attachments):
            return None
        
        attachment = attachments[attachment_index]
        
        # Create download directory if it doesn't exist
        download_path = Path(download_dir)
        download_path.mkdir(exist_ok=True, parents=True)
        
        # Get attachment data
        filename = attachment['filename']
        data = base64.b64decode(attachment['data'])
        
        # Save to file
        file_path = download_path / filename
        with open(file_path, 'wb') as f:
            f.write(data)
        
        return str(file_path)
    
    async def mark_as_read(self, email_id: str, mailbox: str = 'INBOX') -> bool:
        """
        Mark an email as read.
        
        Args:
            email_id: Email ID
            mailbox: Mailbox containing the email
            
        Returns:
            True if email was marked as read successfully, False otherwise
        """
        if not self.imap:
            await self.connect()
        
        try:
            # Select mailbox
            await self.select_mailbox(mailbox)
            
            # Mark as read by removing the \Unseen flag
            result, data = self.imap.store(email_id.encode(), '-FLAGS', '\\Unseen')
            return result == 'OK'
        except Exception as e:
            return False
    
    async def mark_as_unread(self, email_id: str, mailbox: str = 'INBOX') -> bool:
        """
        Mark an email as unread.
        
        Args:
            email_id: Email ID
            mailbox: Mailbox containing the email
            
        Returns:
            True if email was marked as unread successfully, False otherwise
        """
        if not self.imap:
            await self.connect()
        
        try:
            # Select mailbox
            await self.select_mailbox(mailbox)
            
            # Mark as unread by adding the \Unseen flag
            result, data = self.imap.store(email_id.encode(), '+FLAGS', '\\Unseen')
            return result == 'OK'
        except Exception as e:
            return False
