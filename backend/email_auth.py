"""
Email Authentication Module
Handles SPF, DKIM, and DMARC authentication for email sending
"""

import dkim
import spf
import dns.resolver
import socket
import base64
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any
import re
import os

class EmailAuthenticator:
    def __init__(self, domain: str, dkim_selector: str = "default"):
        self.domain = domain
        self.dkim_selector = dkim_selector
        self.dkim_private_key = None
        self.load_dkim_key()
    
    def load_dkim_key(self):
        """Load DKIM private key from file"""
        try:
            key_path = "/app/backend/dkim_private.key"
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    self.dkim_private_key = f.read()
                print(f"DKIM private key loaded for domain: {self.domain}")
            else:
                print(f"DKIM private key not found at {key_path}")
        except Exception as e:
            print(f"Error loading DKIM key: {e}")
    
    def sign_email_with_dkim(self, message: str, from_email: str) -> str:
        """Sign email message with DKIM signature"""
        if not self.dkim_private_key:
            print("DKIM private key not available, skipping DKIM signing")
            return message
        
        try:
            # Extract domain from sender email
            sender_domain = from_email.split('@')[1]
            print(f"Signing email for domain: {sender_domain}")
            
            # Convert message to bytes
            message_bytes = message.encode('utf-8')
            
            # Sign the message
            signature = dkim.sign(
                message_bytes,
                self.dkim_selector.encode('utf-8'),
                sender_domain.encode('utf-8'),
                self.dkim_private_key,
                include_headers=[b'From', b'To', b'Subject', b'Date', b'Message-ID']
            )
            
            # Combine signature with message
            signed_message = signature.decode('utf-8') + message
            print(f"Email signed with DKIM for domain: {sender_domain}")
            return signed_message
            
        except Exception as e:
            print(f"DKIM signing failed: {e}")
            return message
    
    def get_dns_records_for_domain(self, domain: str) -> Dict[str, str]:
        """Generate DNS records needed for email authentication"""
        
        # Get server IP (for SPF record)
        try:
            server_ip = socket.gethostbyname(socket.gethostname())
        except:
            server_ip = "YOUR_SERVER_IP"
        
        # SPF Record
        spf_record = f"v=spf1 ip4:{server_ip} include:_spf.google.com -all"
        
        # DKIM Record (load public key)
        dkim_record = "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7EiQX80du//njh2q3A48KVa3zaTuyQoQhHjsTbWQadYVDDoDFjcWgadx2FEDn97eYXgNAuFGYwLpk40TxsrOXwijMzu0q70BEjhxCU7eaCO67BP4sz1O7u4v0nANDuw3RVvOyCOt0BbXh+zv3wtl7SF3mlVnzgbvm8YJrbnIrd9ZU2VvIdMgEt7+cXUZHu+cBT9u5T7iyrJEHU0qfktfoXVkApKJOONs/DW11HMXg9ALj8871+Sgmv63Z0kZnZCzENu6hMa1/9+nsApVJvpS04uFDwQQZRwMEMAFLBBnf9wXP2oBLgLA/0k4BV1HwgF7Qy+1tPvCxgFGYcE21XIlIwIDAQAB"
        
        # DMARC Record
        dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:dmarc@{domain}; ruf=mailto:dmarc@{domain}; fo=1"
        
        return {
            'spf': {
                'name': f"{domain}",
                'type': 'TXT',
                'value': spf_record
            },
            'dkim': {
                'name': f"{self.dkim_selector}._domainkey.{domain}",
                'type': 'TXT',
                'value': dkim_record
            },
            'dmarc': {
                'name': f"_dmarc.{domain}",
                'type': 'TXT',
                'value': dmarc_record
            }
        }
    
    def build_authenticated_message(self, from_email: str, to_email: str, 
                                  subject: str, body: str, message_id: str,
                                  is_html: bool = False) -> str:
        """Build RFC 5322 compliant email message with authentication headers"""
        
        headers = []
        
        # Core headers
        headers.append(f"Message-ID: <{message_id}@{self.domain}>")
        headers.append(f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}")
        headers.append(f"From: {from_email}")
        headers.append(f"To: {to_email}")
        headers.append(f"Subject: {subject}")
        
        # Authentication-friendly headers
        headers.append(f"Return-Path: <{from_email}>")
        headers.append(f"Reply-To: {from_email}")
        
        # Anti-spam headers
        headers.append("X-Mailer: CustomEmailServer/1.0")
        headers.append("X-Priority: 3")
        headers.append("X-MSMail-Priority: Normal")
        
        # Content headers
        if is_html:
            headers.append("Content-Type: text/html; charset=utf-8")
        else:
            headers.append("Content-Type: text/plain; charset=utf-8")
        
        headers.append("Content-Transfer-Encoding: 8bit")
        headers.append("MIME-Version: 1.0")
        
        # List management headers (helps with spam filtering)
        headers.append(f"List-Unsubscribe: <mailto:unsubscribe@{self.domain}>")
        headers.append(f"List-Unsubscribe-Post: List-Unsubscribe=One-Click")
        
        # Build complete message
        message = "\r\n".join(headers)
        message += "\r\n\r\n"
        message += body
        
        # Sign with DKIM
        signed_message = self.sign_email_with_dkim(message, from_email)
        
        return signed_message