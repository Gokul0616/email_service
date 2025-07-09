from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import json
from bson import ObjectId
import pandas as pd
import io
from fastapi.responses import StreamingResponse
from jinja2 import Template
import re
import bleach

# Import custom modules
from database import get_database
from mongo_encoder import MongoJSONEncoder, custom_jsonable_encoder
from email_relay import EmailRelay
from email_auth import EmailAuthChecker
from models import *
from campaign_service import CampaignService
from email_personalization import EmailPersonalization
from domain_routes import router as domain_router

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

class UserRegistration(BaseModel):
    email: str
    password: str
    full_name: str

# Personalization request models
class PersonalizationRequest(BaseModel):
    content: str
    required_fields: Optional[List[str]] = None

class PersonalizationPreviewRequest(BaseModel):
    content: str

# Unsubscribe request model
class UnsubscribeEmailRequest(BaseModel):
    email: str
    campaign_id: Optional[str] = None
    reason: Optional[str] = None

# Initialize services
email_auth = EmailAuthenticator(domain="pixelrisewebco.com")
email_relay = EmailRelay()
personalizer = EmailPersonalizer()

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

# Enhanced Raw Socket SMTP Client Implementation
class SMTPClient:
    def __init__(self):
        self.dns_resolver = DNSResolver()
        self.socket = None
        self.ssl_socket = None
        self.connected = False
        self.server_capabilities = []
    
    def send_email(self, email: EmailMessage) -> EmailResponse:
        """Send email using raw SMTP protocol with authentication"""
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
            
            # Send email with authentication
            message_id = self._send_smtp_commands(email)
            
            return EmailResponse(
                success=True,
                message=f"Email sent successfully via {mx_server} with DKIM authentication",
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
        """Send SMTP commands to deliver email with authentication"""
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
        
        # Send authenticated message content
        message_id = str(uuid.uuid4())
        
        # Use the email authenticator to build the message with DKIM
        authenticated_message = email_auth.build_authenticated_message(
            email.from_email, email.to_email, email.subject, 
            email.body, message_id, email.is_html
        )
        
        self._send_raw_data(authenticated_message)
        self._send_raw_data("\r\n.\r\n")  # End of message
        
        response = self._read_response()
        if not response.startswith('250'):
            raise Exception(f"Message delivery failed: {response}")
        
        print("Email message delivered successfully with DKIM authentication")
        
        # QUIT command
        self._send_command("QUIT")
        self._read_response()
        
        return message_id
    
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

# Start SMTP server on startup
@app.on_event("startup")
async def startup_event():
    """Start services on application startup"""
    print("Starting Custom Email Server...")
    smtp_server.start_server()
    print("Email authentication system initialized")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop services on application shutdown"""
    smtp_server.stop_server()

# API Endpoints

@app.post("/api/send-email", response_model=EmailResponse)
async def send_email(email: EmailMessage):
    """Send email using professional email relay system"""
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
        
        # Use the professional email relay system
        result = email_relay.send_email_via_relay(
            from_email=email.from_email,
            to_email=email.to_email,
            subject=email.subject,
            body=email.body,
            is_html=email.is_html
        )
        
        # Convert relay result to EmailResponse
        return EmailResponse(
            success=result['success'],
            message=result['message'],
            message_id=result.get('message_id') or result.get('relay_id', str(uuid.uuid4()))
        )
    
    except Exception as e:
        return EmailResponse(
            success=False,
            message=f"Email service error: {str(e)}"
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

@app.get("/api/received-emails")
async def get_received_emails():
    """Get all received emails from SMTP server"""
    try:
        emails = smtp_server.get_all_received_emails()
        return {
            "emails": emails,
            "count": len(emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user-emails/{email_address}")
async def get_user_emails(email_address: str, folder: str = "inbox"):
    """Get emails for a specific user"""
    try:
        emails = smtp_server.get_user_emails(email_address, folder)
        return {
            "user": email_address,
            "folder": folder,
            "emails": emails,
            "count": len(emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/server-status")
async def get_server_status():
    """Get SMTP server status"""
    try:
        status = smtp_server.get_server_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dns-records/{domain}")
async def get_dns_records(domain: str):
    """Get required DNS records for email authentication"""
    try:
        records = email_auth.get_dns_records_for_domain(domain)
        return {
            "domain": domain,
            "records": records,
            "instructions": {
                "spf": "Add this TXT record to your domain's DNS to authorize this server to send emails",
                "dkim": "Add this TXT record to enable DKIM signing for your emails",
                "dmarc": "Add this TXT record to set up DMARC policy for your domain"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth-check/{domain}")
async def check_domain_authentication(domain: str):
    """Check domain authentication status and requirements"""
    try:
        resolver = DNSResolver()
        
        # Check for existing SPF record
        spf_record = None
        try:
            txt_records = resolver.resolver.resolve(domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if txt_value.startswith('v=spf1'):
                    spf_record = txt_value
                    break
        except:
            pass
        
        # Check for existing DKIM record
        dkim_record = None
        try:
            dkim_domain = f"default._domainkey.{domain}"
            txt_records = resolver.resolver.resolve(dkim_domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if 'v=DKIM1' in txt_value:
                    dkim_record = txt_value
                    break
        except:
            pass
        
        # Check for existing DMARC record
        dmarc_record = None
        try:
            dmarc_domain = f"_dmarc.{domain}"
            txt_records = resolver.resolver.resolve(dmarc_domain, 'TXT')
            for record in txt_records:
                txt_value = str(record).strip('"')
                if txt_value.startswith('v=DMARC1'):
                    dmarc_record = txt_value
                    break
        except:
            pass
        
        # Determine authentication status
        auth_status = {
            "spf_configured": spf_record is not None,
            "dkim_configured": dkim_record is not None,
            "dmarc_configured": dmarc_record is not None,
            "fully_authenticated": all([spf_record, dkim_record, dmarc_record])
        }
        
        # Provide setup instructions
        setup_instructions = []
        if not spf_record:
            setup_instructions.append("Set up SPF record to authorize email sending servers")
        if not dkim_record:
            setup_instructions.append("Set up DKIM record for email signing authentication")
        if not dmarc_record:
            setup_instructions.append("Set up DMARC record for email policy enforcement")
        
        return {
            "domain": domain,
            "authentication_status": auth_status,
            "existing_records": {
                "spf": spf_record,
                "dkim": dkim_record,
                "dmarc": dmarc_record
            },
            "setup_required": setup_instructions,
            "ready_for_sending": auth_status["fully_authenticated"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/domain-setup-guide")
async def get_domain_setup():
    """Get complete domain setup guide for pixelrisewebco.com"""
    try:
        guide = get_domain_setup_guide()
        return guide
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/delivery-status/{message_id}")
async def get_delivery_status(message_id: str):
    """Get delivery status for a sent email"""
    try:
        status = email_relay.get_delivery_status(message_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "cold-email-campaign-system",
        "features": [
            "Campaign Management",
            "Contact Management", 
            "Email Templates",
            "A/B Testing",
            "Analytics & Tracking",
            "Email Personalization",
            "DKIM Authentication", 
            "SMTP Server",
            "DNS MX Resolution",
            "Deliverability Optimization"
        ]
    }

# ===========================================
# CAMPAIGN MANAGEMENT ENDPOINTS
# ===========================================

@app.post("/api/campaigns", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate):
    """Create a new email campaign"""
    try:
        result = campaign_service.create_campaign(campaign.dict())
        return CampaignResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns")
async def get_campaigns(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all campaigns with optional filtering"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        
        campaigns = db_manager.get_campaigns(filters, limit, offset)
        
        # Use custom encoder to handle ObjectId
        serialized_campaigns = custom_jsonable_encoder(campaigns)
        
        return MongoJSONEncoder(content={
            "campaigns": serialized_campaigns,
            "total": len(campaigns),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get a specific campaign"""
    try:
        campaign = db_manager.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Use custom encoder to handle ObjectId
        serialized_campaign = custom_jsonable_encoder(campaign)
        
        return MongoJSONEncoder(content=serialized_campaign)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/campaigns/{campaign_id}")
async def update_campaign(campaign_id: str, updates: Dict[str, Any]):
    """Update a campaign"""
    try:
        success = db_manager.update_campaign(campaign_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"success": True, "message": "Campaign updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/campaigns/{campaign_id}")
async def delete_campaign(campaign_id: str):
    """Delete a campaign"""
    try:
        success = db_manager.delete_campaign(campaign_id)
        if not success:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return {"success": True, "message": "Campaign deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/prepare")
async def prepare_campaign(campaign_id: str):
    """Prepare campaign emails for sending"""
    try:
        result = campaign_service.prepare_campaign_emails(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/send")
async def send_campaign(campaign_id: str):
    """Send a campaign"""
    try:
        result = await campaign_service.send_campaign(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/schedule")
async def schedule_campaign(campaign_id: str, scheduled_time: datetime):
    """Schedule a campaign for future sending"""
    try:
        result = campaign_service.schedule_campaign(campaign_id, scheduled_time)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: str):
    """Pause a campaign"""
    try:
        result = campaign_service.pause_campaign(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/campaigns/{campaign_id}/resume")
async def resume_campaign(campaign_id: str):
    """Resume a paused campaign"""
    try:
        result = campaign_service.resume_campaign(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: str):
    """Get campaign statistics"""
    try:
        result = campaign_service.get_campaign_stats(campaign_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/campaigns/{campaign_id}/emails")
async def get_campaign_emails(campaign_id: str, status: Optional[str] = None):
    """Get emails for a campaign"""
    try:
        emails = db_manager.get_campaign_emails(campaign_id, status)
        return {
            "emails": emails,
            "total": len(emails)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# CONTACT MANAGEMENT ENDPOINTS
# ===========================================

@app.post("/api/contacts")
async def create_contact(contact: Contact):
    """Create a new contact"""
    try:
        contact_id = db_manager.create_contact(contact.dict())
        return {"success": True, "message": "Contact created successfully", "contact_id": contact_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contacts")
async def get_contacts(
    status: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all contacts with optional filtering"""
    try:
        filters = {}
        if status:
            filters["status"] = status
        if tag:
            filters["tags"] = {"$in": [tag]}
        
        contacts = db_manager.get_contacts(filters, limit, offset)
        
        # Use custom encoder to handle ObjectId
        serialized_contacts = custom_jsonable_encoder(contacts)
        
        return MongoJSONEncoder(content={
            "contacts": serialized_contacts,
            "total": len(contacts),
            "limit": limit,
            "offset": offset
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contacts/export")
async def export_contacts(format: str = Query("csv", enum=["csv", "excel"])):
    """Export contacts to CSV or Excel"""
    try:
        contacts = db_manager.get_contacts(filters={}, limit=10000)
        
        if not contacts:
            raise HTTPException(status_code=404, detail="No contacts found")
        
        # Convert contacts and handle ObjectId serialization
        serialized_contacts = custom_jsonable_encoder(contacts)
        
        # Create DataFrame
        df = pd.DataFrame(serialized_contacts)
        
        # Remove internal MongoDB fields that shouldn't be exported
        columns_to_remove = ['_id']
        df = df.drop(columns=[col for col in columns_to_remove if col in df.columns])
        
        if format == "csv":
            output = io.StringIO()
            df.to_csv(output, index=False)
            response = Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=contacts.csv"}
            )
            return response
        else:  # excel
            output = io.BytesIO()
            df.to_excel(output, index=False)
            response = Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=contacts.xlsx"}
            )
            return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Get a specific contact"""
    try:
        contact = db_manager.get_contact(contact_id)
        if not contact:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        # Use custom encoder to handle ObjectId
        serialized_contact = custom_jsonable_encoder(contact)
        
        return MongoJSONEncoder(content=serialized_contact)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/contacts/{contact_id}")
async def update_contact(contact_id: str, updates: Dict[str, Any]):
    """Update a contact"""
    try:
        success = db_manager.update_contact(contact_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"success": True, "message": "Contact updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    try:
        success = db_manager.delete_contact(contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"success": True, "message": "Contact deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contacts/bulk-import")
async def bulk_import_contacts(file: UploadFile = File(...)):
    """Bulk import contacts from CSV file"""
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)
        
        # Convert to contacts
        contacts = []
        for row in reader:
            contact_data = {
                "email": row.get("email", "").strip(),
                "first_name": row.get("first_name", "").strip(),
                "last_name": row.get("last_name", "").strip(),
                "company": row.get("company", "").strip(),
                "phone": row.get("phone", "").strip(),
                "tags": [tag.strip() for tag in row.get("tags", "").split(",") if tag.strip()],
                "custom_fields": {k: v for k, v in row.items() if k not in ["email", "first_name", "last_name", "company", "phone", "tags"]}
            }
            
            if contact_data["email"]:
                contact = Contact(**contact_data)
                contacts.append(contact.dict())
        
        # Bulk create
        result = db_manager.bulk_create_contacts(contacts)
        
        return {
            "success": True,
            "message": f"Imported {result['created']} contacts, skipped {result['skipped']} duplicates",
            "created": result["created"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# EMAIL TEMPLATE ENDPOINTS
# ===========================================

@app.post("/api/templates")
async def create_template(template: EmailTemplate):
    """Create a new email template"""
    try:
        template_id = db_manager.create_template(template.dict())
        return {"success": True, "message": "Template created successfully", "template_id": template_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates")
async def get_templates(category: Optional[str] = Query(None)):
    """Get all email templates"""
    try:
        filters = {}
        if category:
            filters["category"] = category
        
        templates = db_manager.get_templates(filters)
        
        # Use custom encoder to handle ObjectId
        serialized_templates = custom_jsonable_encoder(templates)
        
        return MongoJSONEncoder(content={
            "templates": serialized_templates,
            "total": len(templates)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """Get a specific template"""
    try:
        template = db_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Use custom encoder to handle ObjectId
        serialized_template = custom_jsonable_encoder(template)
        
        return MongoJSONEncoder(content=serialized_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/templates/{template_id}")
async def update_template(template_id: str, updates: Dict[str, Any]):
    """Update a template"""
    try:
        success = db_manager.update_template(template_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"success": True, "message": "Template updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/templates/{template_id}")
async def delete_template(template_id: str):
    """Delete a template"""
    try:
        success = db_manager.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
        return {"success": True, "message": "Template deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/templates/{template_id}/preview")
async def preview_template(template_id: str):
    """Preview a template with sample data"""
    try:
        template = db_manager.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Get sample personalization
        sample_subject = personalizer.get_sample_personalization(template["subject"])
        sample_content = personalizer.get_sample_personalization(template["html_content"])
        
        return {
            "subject": sample_subject,
            "html_content": sample_content,
            "variables": personalizer.extract_variables(template["html_content"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# ANALYTICS ENDPOINTS
# ===========================================

@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics():
    """Get dashboard analytics"""
    try:
        stats = db_manager.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/campaigns")
async def get_campaigns_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):
    """Get analytics for all campaigns"""
    try:
        filters = {}
        if start_date:
            filters["created_at"] = {"$gte": start_date}
        if end_date:
            if "created_at" not in filters:
                filters["created_at"] = {}
            filters["created_at"]["$lte"] = end_date
        
        campaigns = db_manager.get_campaigns(filters, limit=1000)
        
        # Calculate aggregate stats
        total_campaigns = len(campaigns)
        total_sent = sum(c.get("sent_count", 0) for c in campaigns)
        total_opens = sum(c.get("opened_count", 0) for c in campaigns)
        total_clicks = sum(c.get("clicked_count", 0) for c in campaigns)
        
        # Use custom encoder to handle ObjectId
        serialized_campaigns = custom_jsonable_encoder(campaigns)
        
        return MongoJSONEncoder(content={
            "total_campaigns": total_campaigns,
            "total_sent": total_sent,
            "total_opens": total_opens,
            "total_clicks": total_clicks,
            "overall_open_rate": (total_opens / total_sent * 100) if total_sent > 0 else 0,
            "overall_click_rate": (total_clicks / total_sent * 100) if total_sent > 0 else 0,
            "campaigns": serialized_campaigns
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# EMAIL PERSONALIZATION ENDPOINTS
# ===========================================

@app.post("/api/personalization/validate")
async def validate_personalization(request: PersonalizationRequest):
    """Validate email content for personalization"""
    try:
        result = personalizer.validate_content(request.content, request.required_fields)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/personalization/preview")
async def preview_personalization(request: PersonalizationPreviewRequest):
    """Preview personalized content with sample data"""
    try:
        sample = personalizer.get_sample_personalization(request.content)
        variables = personalizer.extract_variables(request.content)
        stats = personalizer.get_personalization_stats(request.content)
        
        return {
            "original": request.content,
            "personalized": sample,
            "variables": variables,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# TRACKING ENDPOINTS
# ===========================================

@app.get("/api/track/open/{tracking_id}")
async def track_email_open(tracking_id: str, request: Request):
    """Track email opens"""
    try:
        # Get client info
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Update email status
        db_manager.update_campaign_email(tracking_id, {
            "status": "opened",
            "opened_at": datetime.now(),
            "open_count": 1  # This would be incremented in a real implementation
        })
        
        # Create analytics event
        analytics_data = {
            "email_id": tracking_id,
            "event_type": "open",
            "event_timestamp": datetime.now(),
            "ip_address": client_ip,
            "user_agent": user_agent
        }
        
        analytics_event = EmailAnalytics(**analytics_data)
        db_manager.create_analytics_event(analytics_event.dict())
        
        # Return 1x1 transparent pixel
        pixel_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==")
        return Response(content=pixel_data, media_type="image/png")
    except Exception as e:
        return Response(content=pixel_data, media_type="image/png")  # Still return pixel even on error

@app.get("/api/track/click/{tracking_id}")
async def track_email_click(tracking_id: str, url: str, request: Request):
    """Track email clicks"""
    try:
        # Get client info
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        # Update email status
        db_manager.update_campaign_email(tracking_id, {
            "status": "clicked",
            "clicked_at": datetime.now(),
            "click_count": 1  # This would be incremented in a real implementation
        })
        
        # Create analytics event
        analytics_data = {
            "email_id": tracking_id,
            "event_type": "click",
            "event_timestamp": datetime.now(),
            "ip_address": client_ip,
            "user_agent": user_agent,
            "click_url": url
        }
        
        analytics_event = EmailAnalytics(**analytics_data)
        db_manager.create_analytics_event(analytics_event.dict())
        
        # Redirect to original URL
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        # Even on error, redirect to the original URL
        return RedirectResponse(url=url, status_code=302)

@app.post("/api/unsubscribe")
async def unsubscribe_email(request: UnsubscribeEmailRequest):
    """Handle email unsubscribe"""
    try:
        # Create unsubscribe record
        unsubscribe_data = {
            "email": request.email,
            "campaign_id": request.campaign_id,
            "reason": request.reason
        }
        
        unsubscribe_record = UnsubscribeRequest(**unsubscribe_data)
        db_manager.create_unsubscribe(unsubscribe_record.dict())
        
        return {"success": True, "message": "Email unsubscribed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/unsubscribe/{email}")
async def unsubscribe_page(email: str):
    """Unsubscribe confirmation page"""
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Unsubscribe Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .container {{ text-align: center; }}
                .button {{ background-color: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }}
                .success {{ color: green; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Unsubscribe from Email List</h2>
                <p>Click the button below to unsubscribe {email} from all future emails.</p>
                <button class="button" onclick="unsubscribe()">Unsubscribe</button>
                <div id="result"></div>
            </div>
            <script>
                function unsubscribe() {{
                    fetch('/api/unsubscribe', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ email: '{email}', reason: 'User requested' }})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        document.getElementById('result').innerHTML = '<p class="success">You have been unsubscribed successfully.</p>';
                    }})
                    .catch(error => {{
                        document.getElementById('result').innerHTML = '<p>Error: ' + error.message + '</p>';
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================
# LEGACY ENDPOINTS (keep for compatibility)
# ===========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)