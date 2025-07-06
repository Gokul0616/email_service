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
        self.fallback_smtp_config = {
            'smtp.gmail.com': {'port': 587, 'tls': True},
            'smtp.yahoo.com': {'port': 587, 'tls': True},
            'smtp.outlook.com': {'port': 587, 'tls': True}
        }
    
    def load_dkim_key(self):
        """Load DKIM private key from file"""
        try:
            # Try domain-specific key first
            domain_key_path = f"/app/backend/dkim_private_{self.domain.replace('.', '_')}.key"
            if os.path.exists(domain_key_path):
                with open(domain_key_path, 'rb') as f:
                    self.dkim_private_key = f.read()
                print(f"DKIM private key loaded for domain: {self.domain}")
                return
            
            # Fallback to default key
            key_path = "/app/backend/dkim_private.key"
            if os.path.exists(key_path):
                with open(key_path, 'rb') as f:
                    self.dkim_private_key = f.read()
                print(f"Default DKIM private key loaded for domain: {self.domain}")
            else:
                print(f"DKIM private key not found, will generate temporary key")
        except Exception as e:
            print(f"Error loading DKIM key: {e}")
    
    def sign_email_with_dkim(self, message: str, from_email: str) -> str:
        """Sign email message with DKIM signature using sender's domain"""
        try:
            # Extract domain from sender email
            sender_domain = from_email.split('@')[1]
            print(f"Signing email for domain: {sender_domain}")
            
            # If no private key available, generate one for this domain
            if not self.dkim_private_key:
                print("No DKIM private key available - generating temporary key")
                self.dkim_private_key = self._generate_temp_dkim_key()
            
            # Convert message to bytes
            message_bytes = message.encode('utf-8')
            
            # Sign the message with sender's domain
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
            # Return original message if signing fails
            return message
    
    def _generate_temp_dkim_key(self) -> bytes:
        """Generate a temporary DKIM key for testing"""
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            
            # Generate a new RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Serialize private key
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            print("Generated temporary DKIM key for testing")
            return private_pem
            
        except Exception as e:
            print(f"Failed to generate temporary DKIM key: {e}")
            # Return existing key if generation fails
            try:
                with open("/app/backend/dkim_private.key", 'rb') as f:
                    return f.read()
            except:
                return None
    
    def get_dns_records_for_domain(self, domain: str) -> Dict[str, str]:
        """Generate DNS records needed for email authentication"""
        
        # Get server IP (for SPF record)
        try:
            server_ip = socket.gethostbyname(socket.gethostname())
        except:
            server_ip = "YOUR_SERVER_IP"
        
        # SPF Record - Include your server IP and common email services
        spf_record = f"v=spf1 ip4:{server_ip} include:_spf.google.com include:mailgun.org include:_spf.mailjet.com -all"
        
        # DKIM Record - Load the actual public key we generated
        dkim_record = self._get_dkim_public_key_record(domain)
        
        # DMARC Record - Production-ready policy
        dmarc_record = f"v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@{domain}; ruf=mailto:dmarc-failures@{domain}; fo=1; adkim=r; aspf=r"
        
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
    
    def _get_dkim_public_key_record(self, domain: str) -> str:
        """Get DKIM public key record for domain"""
        try:
            # Try to load the actual generated public key
            domain_key_path = f"/app/backend/dkim_public_{domain.replace('.', '_')}.key"
            if os.path.exists(domain_key_path):
                with open(domain_key_path, 'rb') as f:
                    public_key_pem = f.read()
                
                # Convert PEM to DKIM format
                from cryptography.hazmat.primitives import serialization
                import base64
                
                public_key = serialization.load_pem_public_key(public_key_pem)
                public_key_der = public_key.public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                public_key_b64 = base64.b64encode(public_key_der).decode('ascii')
                
                return f"v=DKIM1; k=rsa; p={public_key_b64}"
            
        except Exception as e:
            print(f"Error loading DKIM public key: {e}")
        
        # Fallback to default record
        return "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAv4Ot69Tpf34KzPIGAp7h3yo8zFH3vetICe/O81pJkW9FA3VyqNy5fgzXvIrmSkUfBvW3qkdYqmUMPeoucXei+QvZQprQPvfZEPuRs1sjdAPRx/G3obTiQZGfxLt0aanz2b6jQ5s0p5ULx0xSL3OU4YIw65G41fa7vT09TXxGjyosdy87RTLBMe49Sxi4C72eYoLvT9TaVNl1TtguND3nLZtiRfG0N61W8u/wZ9vLWhQ8sSxYI+OmwTDUQWtP72zVBfhpimsAx1jGcf+t566qO7NYF97DPk0jOTUOlKnvTlfL810TLjtCN8Zwf29enFMRHT9k3OVnbhknI+S6K0NPfwIDAQAB"
    
    def build_authenticated_message(self, from_email: str, to_email: str, 
                                  subject: str, body: str, message_id: str,
                                  is_html: bool = False) -> str:
        """Build RFC 5322 compliant email message with authentication headers"""
        
        # Extract sender domain for authentication
        sender_domain = from_email.split('@')[1]
        
        headers = []
        
        # Core headers
        headers.append(f"Message-ID: <{message_id}@{sender_domain}>")
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
        headers.append(f"List-Unsubscribe: <mailto:unsubscribe@{sender_domain}>")
        headers.append(f"List-Unsubscribe-Post: List-Unsubscribe=One-Click")
        
        # Build complete message
        message = "\r\n".join(headers)
        message += "\r\n\r\n"
        message += body
        
        # Sign with DKIM using sender domain
        signed_message = self.sign_email_with_dkim(message, from_email)
        
        return signed_message