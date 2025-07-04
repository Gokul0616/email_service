from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import socket
import ssl
import struct
import base64
import uuid
import re
from datetime import datetime
from typing import List, Optional
import json

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class EmailMessage(BaseModel):
    to_email: str
    from_email: str
    from_name: str
    subject: str
    body: str
    is_html: bool = False

class EmailResponse(BaseModel):
    success: bool
    message: str
    message_id: Optional[str] = None

# DNS MX Record Lookup Implementation
class DNSResolver:
    def __init__(self):
        self.dns_servers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
    
    def query_mx_records(self, domain: str) -> List[tuple]:
        """Query MX records for a domain using raw DNS protocol"""
        for dns_server in self.dns_servers:
            try:
                return self._query_mx_from_server(domain, dns_server)
            except Exception as e:
                print(f"Failed to query {dns_server}: {e}")
                continue
        raise Exception(f"Failed to resolve MX records for {domain}")
    
    def _query_mx_from_server(self, domain: str, dns_server: str) -> List[tuple]:
        """Send raw DNS query for MX records"""
        # Create DNS query packet
        query_id = struct.pack('>H', 0x1234)  # Query ID
        flags = struct.pack('>H', 0x0100)    # Standard query
        questions = struct.pack('>H', 1)     # Number of questions
        answers = struct.pack('>H', 0)       # Number of answers
        authority = struct.pack('>H', 0)     # Number of authority records
        additional = struct.pack('>H', 0)    # Number of additional records
        
        # Build question section
        question = self._build_dns_question(domain, 15)  # 15 = MX record type
        
        # Complete DNS packet
        dns_packet = query_id + flags + questions + answers + authority + additional + question
        
        # Send DNS query
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        try:
            sock.sendto(dns_packet, (dns_server, 53))
            response, _ = sock.recvfrom(1024)
            return self._parse_mx_response(response)
        finally:
            sock.close()
    
    def _build_dns_question(self, domain: str, qtype: int) -> bytes:
        """Build DNS question section"""
        question = b''
        
        # Encode domain name
        for part in domain.split('.'):
            question += struct.pack('B', len(part)) + part.encode('ascii')
        question += b'\x00'  # End of domain name
        
        # Add question type (MX = 15) and class (IN = 1)
        question += struct.pack('>HH', qtype, 1)
        
        return question
    
    def _parse_mx_response(self, response: bytes) -> List[tuple]:
        """Parse DNS response and extract MX records"""
        if len(response) < 12:
            raise Exception("Invalid DNS response")
        
        # Parse header
        header = struct.unpack('>HHHHHH', response[:12])
        answer_count = header[3]
        
        if answer_count == 0:
            return []
        
        # Skip question section
        offset = 12
        while offset < len(response) and response[offset] != 0:
            if response[offset] >= 192:  # Compression pointer
                offset += 2
                break
            offset += response[offset] + 1
        offset += 5  # Skip null terminator and question type/class
        
        # Parse answer section
        mx_records = []
        for _ in range(answer_count):
            if offset >= len(response):
                break
            
            # Skip name (can be compressed)
            if response[offset] >= 192:
                offset += 2
            else:
                while offset < len(response) and response[offset] != 0:
                    offset += response[offset] + 1
                offset += 1
            
            if offset + 10 > len(response):
                break
            
            # Parse answer header
            answer_header = struct.unpack('>HHIHH', response[offset:offset+10])
            record_type = answer_header[0]
            data_length = answer_header[4]
            offset += 10
            
            if record_type == 15 and offset + data_length <= len(response):  # MX record
                priority = struct.unpack('>H', response[offset:offset+2])[0]
                offset += 2
                
                # Parse MX hostname
                hostname = self._parse_domain_name(response, offset)
                mx_records.append((priority, hostname))
                offset += data_length - 2
            else:
                offset += data_length
        
        return sorted(mx_records, key=lambda x: x[0])  # Sort by priority
    
    def _parse_domain_name(self, response: bytes, offset: int) -> str:
        """Parse domain name from DNS response (handles compression)"""
        parts = []
        original_offset = offset
        jumped = False
        
        while offset < len(response):
            length = response[offset]
            
            if length == 0:
                break
            elif length >= 192:  # Compression pointer
                if not jumped:
                    original_offset = offset + 2
                    jumped = True
                offset = ((length & 0x3F) << 8) | response[offset + 1]
            else:
                offset += 1
                if offset + length > len(response):
                    break
                parts.append(response[offset:offset+length].decode('ascii'))
                offset += length
        
        return '.'.join(parts)

# Raw Socket SMTP Client Implementation
class SMTPClient:
    def __init__(self):
        self.dns_resolver = DNSResolver()
        self.socket = None
        self.ssl_socket = None
        self.connected = False
        self.authenticated = False
    
    def send_email(self, email: EmailMessage) -> EmailResponse:
        """Send email using raw SMTP protocol"""
        try:
            # Extract domain from recipient email
            recipient_domain = email.to_email.split('@')[1]
            
            # Get MX records for recipient domain
            mx_records = self.dns_resolver.query_mx_records(recipient_domain)
            
            if not mx_records:
                raise Exception(f"No MX records found for {recipient_domain}")
            
            # Try each MX server in order of priority
            last_error = None
            for priority, mx_server in mx_records:
                try:
                    return self._send_via_mx_server(mx_server, email)
                except Exception as e:
                    last_error = e
                    print(f"Failed to send via {mx_server}: {e}")
                    continue
            
            raise Exception(f"Failed to send email via any MX server. Last error: {last_error}")
        
        except Exception as e:
            return EmailResponse(success=False, message=str(e))
    
    def _send_via_mx_server(self, mx_server: str, email: EmailMessage) -> EmailResponse:
        """Send email via specific MX server"""
        try:
            # Connect to MX server
            self._connect(mx_server, 25)
            
            # SMTP handshake
            self._smtp_handshake(email.from_email.split('@')[1])
            
            # Start TLS if supported
            self._start_tls_if_supported()
            
            # Send email
            message_id = self._send_smtp_commands(email)
            
            return EmailResponse(
                success=True,
                message=f"Email sent successfully via {mx_server}",
                message_id=message_id
            )
        
        finally:
            self._disconnect()
    
    def _connect(self, host: str, port: int = 25):
        """Connect to SMTP server using raw socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(30)
        
        try:
            self.socket.connect((host, port))
            self.connected = True
            
            # Read server greeting
            response = self._read_response()
            if not response.startswith('220'):
                raise Exception(f"Server rejected connection: {response}")
        
        except Exception as e:
            self._disconnect()
            raise Exception(f"Failed to connect to {host}:{port} - {e}")
    
    def _smtp_handshake(self, sender_domain: str):
        """Perform SMTP handshake"""
        # Send EHLO command
        self._send_command(f"EHLO {sender_domain}")
        response = self._read_response()
        
        if not response.startswith('250'):
            # Try HELO if EHLO fails
            self._send_command(f"HELO {sender_domain}")
            response = self._read_response()
            if not response.startswith('250'):
                raise Exception(f"SMTP handshake failed: {response}")
        
        # Parse server capabilities
        self.server_capabilities = response.split('\n')
    
    def _start_tls_if_supported(self):
        """Start TLS if server supports it"""
        if any('STARTTLS' in cap for cap in self.server_capabilities):
            self._send_command("STARTTLS")
            response = self._read_response()
            
            if response.startswith('220'):
                # Wrap socket with TLS
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                self.ssl_socket = context.wrap_socket(self.socket, server_hostname=None)
                self.socket = self.ssl_socket
                
                print("TLS connection established")
    
    def _send_smtp_commands(self, email: EmailMessage) -> str:
        """Send SMTP commands to deliver email"""
        # MAIL FROM command
        self._send_command(f"MAIL FROM:<{email.from_email}>")
        response = self._read_response()
        if not response.startswith('250'):
            raise Exception(f"MAIL FROM failed: {response}")
        
        # RCPT TO command
        self._send_command(f"RCPT TO:<{email.to_email}>")
        response = self._read_response()
        if not response.startswith('250'):
            raise Exception(f"RCPT TO failed: {response}")
        
        # DATA command
        self._send_command("DATA")
        response = self._read_response()
        if not response.startswith('354'):
            raise Exception(f"DATA command failed: {response}")
        
        # Send message content
        message_id = str(uuid.uuid4())
        message_content = self._build_email_message(email, message_id)
        
        self._send_raw_data(message_content)
        self._send_raw_data("\r\n.\r\n")  # End of message
        
        response = self._read_response()
        if not response.startswith('250'):
            raise Exception(f"Message delivery failed: {response}")
        
        # QUIT command
        self._send_command("QUIT")
        self._read_response()
        
        return message_id
    
    def _build_email_message(self, email: EmailMessage, message_id: str) -> str:
        """Build RFC 5322 compliant email message"""
        headers = []
        
        # Required headers
        headers.append(f"Message-ID: <{message_id}@custom-mail-server>")
        headers.append(f"Date: {datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}")
        headers.append(f"From: {email.from_name} <{email.from_email}>")
        headers.append(f"To: {email.to_email}")
        headers.append(f"Subject: {email.subject}")
        
        # MIME headers
        if email.is_html:
            headers.append("Content-Type: text/html; charset=utf-8")
        else:
            headers.append("Content-Type: text/plain; charset=utf-8")
        
        headers.append("Content-Transfer-Encoding: 8bit")
        headers.append("MIME-Version: 1.0")
        
        # Build complete message
        message = "\r\n".join(headers)
        message += "\r\n\r\n"
        message += email.body
        
        return message
    
    def _send_command(self, command: str):
        """Send SMTP command"""
        self._send_raw_data(command + "\r\n")
        print(f"SENT: {command}")
    
    def _send_raw_data(self, data: str):
        """Send raw data to server"""
        if self.socket:
            self.socket.sendall(data.encode('utf-8'))
    
    def _read_response(self) -> str:
        """Read SMTP server response"""
        if not self.socket:
            raise Exception("Not connected to server")
        
        response = b''
        while True:
            chunk = self.socket.recv(1024)
            if not chunk:
                break
            response += chunk
            
            # Check if we have a complete response
            if b'\r\n' in response:
                break
        
        decoded_response = response.decode('utf-8').strip()
        print(f"RECV: {decoded_response}")
        return decoded_response
    
    def _disconnect(self):
        """Disconnect from server"""
        if self.ssl_socket:
            self.ssl_socket.close()
        if self.socket:
            self.socket.close()
        
        self.socket = None
        self.ssl_socket = None
        self.connected = False
        self.authenticated = False

# Initialize SMTP client
smtp_client = SMTPClient()

# API Endpoints
@app.post("/api/send-email", response_model=EmailResponse)
async def send_email(email: EmailMessage):
    """Send email using custom SMTP client"""
    try:
        # Basic validation
        if not email.to_email or '@' not in email.to_email:
            raise HTTPException(status_code=400, detail="Invalid recipient email")
        
        if not email.from_email or '@' not in email.from_email:
            raise HTTPException(status_code=400, detail="Invalid sender email")
        
        # Send email
        result = smtp_client.send_email(email)
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.message)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-mx/{domain}")
async def test_mx_lookup(domain: str):
    """Test MX record lookup for a domain"""
    try:
        resolver = DNSResolver()
        mx_records = resolver.query_mx_records(domain)
        
        return {
            "domain": domain,
            "mx_records": [{"priority": priority, "server": server} for priority, server in mx_records]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "custom-email-server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)