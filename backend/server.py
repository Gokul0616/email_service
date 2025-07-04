from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import socket
import ssl
import dns.resolver
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
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = ['8.8.8.8', '1.1.1.1', '8.8.4.4']
        self.resolver.timeout = 5
        self.resolver.lifetime = 10
    
    def query_mx_records(self, domain: str) -> List[tuple]:
        """Query MX records for a domain"""
        try:
            mx_records = self.resolver.resolve(domain, 'MX')
            return [(record.preference, str(record.exchange).rstrip('.')) for record in mx_records]
        except Exception as e:
            raise Exception(f"Failed to resolve MX records for {domain}: {str(e)}")

# Raw Socket SMTP Client Implementation
class SMTPClient:
    def __init__(self):
        self.dns_resolver = DNSResolver()
        self.socket = None
        self.ssl_socket = None
        self.connected = False
        self.server_capabilities = []
    
    def send_email(self, email: EmailMessage) -> EmailResponse:
        """Send email using raw SMTP protocol"""
        try:
            # Extract domain from recipient email
            recipient_domain = email.to_email.split('@')[1]
            
            # Get MX records for recipient domain
            mx_records = self.dns_resolver.query_mx_records(recipient_domain)
            
            if not mx_records:
                return EmailResponse(
                    success=False, 
                    message=f"No MX records found for {recipient_domain}. Domain may not accept email."
                )
            
            # Sort by priority (lower number = higher priority)
            mx_records.sort(key=lambda x: x[0])
            
            # Try each MX server in order of priority
            last_error = None
            for priority, mx_server in mx_records:
                try:
                    print(f"Attempting to send via {mx_server} (priority {priority})")
                    return self._send_via_mx_server(mx_server, email)
                except Exception as e:
                    last_error = e
                    print(f"Failed to send via {mx_server}: {e}")
                    continue
            
            # Provide more specific error messages based on the last error
            error_message = str(last_error)
            if "550" in error_message:
                return EmailResponse(
                    success=False,
                    message=f"Email rejected by recipient server: {error_message}. The email address may not exist or is refusing mail."
                )
            elif "553" in error_message:
                return EmailResponse(
                    success=False,
                    message=f"Email rejected due to sender policy: {error_message}. The sender address may be blocked or invalid."
                )
            elif "Connection refused" in error_message or "timed out" in error_message:
                return EmailResponse(
                    success=False,
                    message=f"Unable to connect to mail servers for {recipient_domain}: {error_message}"
                )
            else:
                return EmailResponse(
                    success=False,
                    message=f"Failed to send email via any MX server: {error_message}"
                )
        
        except Exception as e:
            print(f"Email sending error: {e}")
            return EmailResponse(
                success=False, 
                message=f"Email service error: {str(e)}"
            )
    
    def _send_via_mx_server(self, mx_server: str, email: EmailMessage) -> EmailResponse:
        """Send email via specific MX server"""
        try:
            # Connect to MX server
            self._connect(mx_server, 25)
            
            # SMTP handshake
            self._smtp_handshake(email.from_email.split('@')[1])
            
            # Start TLS if supported
            self._start_tls_if_supported(mx_server)
            
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
            print(f"Connecting to {host}:{port}")
            self.socket.connect((host, port))
            self.connected = True
            
            # Read server greeting
            response = self._read_response()
            print(f"Server greeting: {response}")
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
        print(f"Server capabilities: {len(self.server_capabilities)} features")
    
    def _start_tls_if_supported(self, hostname: str):
        """Start TLS if server supports it"""
        if any('STARTTLS' in cap for cap in self.server_capabilities):
            print("STARTTLS is supported, initiating TLS")
            self._send_command("STARTTLS")
            response = self._read_response()
            
            if response.startswith('220'):
                # Wrap socket with TLS
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                self.ssl_socket = context.wrap_socket(self.socket, server_hostname=hostname)
                self.socket = self.ssl_socket
                
                print("TLS connection established successfully")
                
                # Re-send EHLO after TLS
                self._smtp_handshake(hostname)
            else:
                print(f"STARTTLS failed: {response}")
        else:
            print("STARTTLS not supported by server")
    
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
        
        print("Email message delivered successfully")
        
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
            try:
                chunk = self.socket.recv(1024)
                if not chunk:
                    break
                response += chunk
                
                # Check if we have a complete response
                if b'\r\n' in response:
                    # Handle multi-line responses
                    lines = response.decode('utf-8').split('\r\n')
                    if lines[-1] == '':
                        lines = lines[:-1]
                    
                    # Check if last line indicates end of response
                    if lines and len(lines[-1]) >= 4 and lines[-1][3] == ' ':
                        break
                    
                    # Continue reading if there's more data
                    if len(lines) == 1:
                        break
                        
            except socket.timeout:
                break
            except Exception as e:
                print(f"Error reading response: {e}")
                break
        
        decoded_response = response.decode('utf-8').strip()
        print(f"RECV: {decoded_response}")
        return decoded_response
    
    def _disconnect(self):
        """Disconnect from server"""
        try:
            if self.ssl_socket:
                self.ssl_socket.close()
            if self.socket:
                self.socket.close()
        except:
            pass
        
        self.socket = None
        self.ssl_socket = None
        self.connected = False

# Initialize SMTP client
smtp_client = SMTPClient()

# API Endpoints
@app.post("/api/send-email", response_model=EmailResponse)
async def send_email(email: EmailMessage):
    """Send email using custom SMTP client"""
    try:
        # Basic validation
        if not email.to_email or '@' not in email.to_email:
            return EmailResponse(
                success=False,
                message="Invalid recipient email address format"
            )
        
        if not email.from_email or '@' not in email.from_email:
            return EmailResponse(
                success=False,
                message="Invalid sender email address format"
            )
        
        # Send email
        result = smtp_client.send_email(email)
        return result
    
    except Exception as e:
        return EmailResponse(
            success=False,
            message=f"Unexpected error: {str(e)}"
        )

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