import requests
import json
import sys
import time
import random
import string
import csv
import io
from datetime import datetime, timedelta

class EmailServiceTester:
    def __init__(self, base_url="https://4b5c7461-d5f7-4e38-b7c8-06e9cec90cb8.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.created_contacts = []
        self.created_templates = []
        self.created_campaigns = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, data=data)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            
            # Print response details for debugging
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                result = {"name": name, "status": "PASS", "details": "Test passed successfully"}
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                result = {"name": name, "status": "FAIL", "details": f"Expected status {expected_status}, got {response.status_code}"}
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
            
            self.test_results.append(result)
            return success, response
        
        except Exception as e:
            result = {"name": name, "status": "ERROR", "details": str(e)}
            self.test_results.append(result)
            print(f"❌ Error - {str(e)}")
            return False, None

    def test_health_endpoint(self):
        """Test the health check endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "/api/health",
            200
        )
        if success:
            data = response.json()
            if data.get("status") == "healthy" and data.get("service") == "cold-email-campaign-system":
                print("✅ Health check response content verified")
                return True
            else:
                print("❌ Health check response content incorrect")
                return False
        return False

    def test_mx_lookup(self, domain):
        """Test MX record lookup for a domain"""
        success, response = self.run_test(
            f"MX Lookup for {domain}",
            "GET",
            f"/api/test-mx/{domain}",
            200
        )
        if success:
            data = response.json()
            if "mx_records" in data and isinstance(data["mx_records"], list):
                print(f"✅ Found {len(data['mx_records'])} MX records for {domain}")
                for record in data["mx_records"]:
                    print(f"  - Priority: {record['priority']}, Server: {record['server']}")
                return True
            else:
                print("❌ MX lookup response format incorrect")
                return False
        return False
    
    def test_mx_lookup_nonexistent(self, domain):
        """Test MX record lookup for a non-existent domain"""
        success, response = self.run_test(
            f"MX Lookup for non-existent domain {domain}",
            "GET",
            f"/api/test-mx/{domain}",
            500  # Expecting error for non-existent domain
        )
        # This should fail with a 500 error for non-existent domains
        if success:
            print("✅ Properly handled non-existent domain with error response")
            return True
        return False

    def test_send_email(self, to_email, from_email, from_name, subject, body, expected_success=True, error_check=None):
        """Test sending an email with error handling validation"""
        data = {
            "to_email": to_email,
            "from_email": from_email,
            "from_name": from_name,
            "subject": subject,
            "body": body,
            "is_html": False
        }
        
        success, response = self.run_test(
            f"Send Email to {to_email}",
            "POST",
            "/api/send-email",
            200,  # We expect 200 even for error responses now
            data=data
        )
        
        if not success:
            return False
            
        response_data = response.json()
        
        # Check if the success flag matches our expectation
        if response_data.get("success") == expected_success:
            if expected_success:
                if response_data.get("message_id"):
                    print(f"✅ Email sent successfully with message ID: {response_data['message_id']}")
                    return True
                else:
                    print("❌ Email sending response missing message_id")
                    return False
            else:
                # For expected failures, check if we have a proper error message
                if response_data.get("message") and len(response_data.get("message")) > 0:
                    print(f"✅ Expected failure with proper error message: {response_data['message']}")
                    
                    # If we have a specific error message to check for
                    if error_check and error_check.lower() in response_data.get("message").lower():
                        print(f"✅ Error message contains expected text: '{error_check}'")
                    elif error_check:
                        print(f"❌ Error message doesn't contain expected text: '{error_check}'")
                        return False
                        
                    return True
                else:
                    print("❌ Expected failure but no proper error message provided")
                    return False
        else:
            if expected_success:
                print(f"❌ Expected success but got failure: {response_data.get('message', 'No error message')}")
            else:
                print(f"❌ Expected failure but got success")
            return False

    def test_invalid_email_format(self):
        """Test sending email with invalid email format"""
        data = {
            "to_email": "invalid-email",  # Invalid email format
            "from_email": "test@example.com",
            "from_name": "Test User",
            "subject": "Test Invalid Format",
            "body": "This email has an invalid recipient format."
        }
        
        success, response = self.run_test(
            "Send Email with Invalid Format",
            "POST",
            "/api/send-email",
            200,  # We expect 200 with error details
            data=data
        )
        
        if success:
            data = response.json()
            if not data.get("success") and "invalid" in data.get("message", "").lower():
                print(f"✅ Properly rejected invalid email format with message: {data['message']}")
                return True
            else:
                print("❌ Did not properly handle invalid email format")
                return False
        return False
    
    def test_received_emails(self):
        """Test getting all received emails"""
        success, response = self.run_test(
            "Get All Received Emails",
            "GET",
            "/api/received-emails",
            200
        )
        
        if success:
            data = response.json()
            if "emails" in data and "count" in data:
                print(f"✅ Retrieved {data['count']} received emails")
                return True
            else:
                print("❌ Received emails response format incorrect")
                return False
        return False
    
    def test_user_emails(self, email_address, folder="inbox"):
        """Test getting user-specific emails"""
        success, response = self.run_test(
            f"Get User Emails for {email_address}",
            "GET",
            f"/api/user-emails/{email_address}?folder={folder}",
            200
        )
        
        if success:
            data = response.json()
            if "emails" in data and "count" in data and "user" in data and "folder" in data:
                print(f"✅ Retrieved {data['count']} emails for user {email_address} in folder {folder}")
                return True
            else:
                print("❌ User emails response format incorrect")
                return False
        return False
    
    def test_server_status(self):
        """Test getting SMTP server status"""
        success, response = self.run_test(
            "Get Server Status",
            "GET",
            "/api/server-status",
            200
        )
        
        if success:
            data = response.json()
            if "running" in data and "host" in data and "port" in data:
                print(f"✅ Server status: Running={data['running']}, Host={data['host']}, Port={data['port']}")
                return True
            else:
                print("❌ Server status response format incorrect")
                return False
        return False
    
    def test_dns_records(self, domain):
        """Test getting DNS records for a domain"""
        success, response = self.run_test(
            f"Get DNS Records for {domain}",
            "GET",
            f"/api/dns-records/{domain}",
            200
        )
        
        if success:
            data = response.json()
            if "domain" in data and "records" in data and "instructions" in data:
                print(f"✅ Retrieved DNS records for domain {domain}")
                # Check if we have the expected record types
                records = data["records"]
                if "spf" in records and "dkim" in records and "dmarc" in records:
                    print("✅ All required DNS record types (SPF, DKIM, DMARC) are present")
                    return True
                else:
                    print("❌ Missing some required DNS record types")
                    return False
            else:
                print("❌ DNS records response format incorrect")
                return False
        return False
        
    def test_auth_check(self, domain):
        """Test domain authentication status check"""
        success, response = self.run_test(
            f"Authentication Check for {domain}",
            "GET",
            f"/api/auth-check/{domain}",
            200
        )
        
        if success:
            data = response.json()
            if "domain" in data and "authentication_status" in data and "existing_records" in data:
                print(f"✅ Retrieved authentication status for domain {domain}")
                auth_status = data["authentication_status"]
                print(f"  - SPF Configured: {auth_status.get('spf_configured', False)}")
                print(f"  - DKIM Configured: {auth_status.get('dkim_configured', False)}")
                print(f"  - DMARC Configured: {auth_status.get('dmarc_configured', False)}")
                print(f"  - Fully Authenticated: {auth_status.get('fully_authenticated', False)}")
                
                if "setup_required" in data and isinstance(data["setup_required"], list):
                    print(f"  - Setup Required: {', '.join(data['setup_required'])}")
                
                return True
            else:
                print("❌ Authentication check response format incorrect")
                return False
        return False

    def test_send_email_to_real_address(self, to_email, from_email, from_name, subject, body, expected_success=False):
        """Test sending an email to a real address"""
        print(f"\n🔍 Testing email sending to real address: {to_email}")
        print(f"  - From: {from_email}")
        
        data = {
            "to_email": to_email,
            "from_email": from_email,
            "from_name": from_name,
            "subject": subject,
            "body": body,
            "is_html": False
        }
        
        success, response = self.run_test(
            f"Send Email to Real Address {to_email}",
            "POST",
            "/api/send-email",
            200,
            data=data
        )
        
        if not success:
            return False
            
        response_data = response.json()
        
        # Check for authentication warnings in the response
        if not response_data.get("success"):
            error_message = response_data.get("message", "")
            print(f"  - Error Message: {error_message}")
            
            # Check for improved error messaging
            auth_keywords = ["authentication", "spf", "dkim", "dmarc", "dns"]
            has_auth_guidance = any(keyword in error_message.lower() for keyword in auth_keywords)
            
            if has_auth_guidance:
                print("✅ Response includes authentication guidance")
            else:
                print("❌ Response missing authentication guidance")
            
            # This is expected to fail, so return True if we got a proper error message
            return len(error_message) > 0
        else:
            # If it succeeded (unlikely), that's fine too
            print(f"✅ Email sent successfully with message ID: {response_data.get('message_id', 'unknown')}")
            return True
            
    # Campaign Management API Tests
    def test_create_campaign(self, name, subject, html_content, from_email, from_name):
        """Test creating a new campaign"""
        data = {
            "name": name,
            "subject": subject,
            "html_content": html_content,
            "text_content": "Plain text version of the email",
            "from_email": from_email,
            "from_name": from_name,
            "contact_lists": [],
            "tags": ["test", "api"],
            "send_immediately": False
        }
        
        success, response = self.run_test(
            "Create Campaign",
            "POST",
            "/api/campaigns",
            200,
            data=data
        )
        
        if success:
            response_data = response.json()
            if response_data.get("success") and response_data.get("campaign_id"):
                print(f"✅ Campaign created with ID: {response_data['campaign_id']}")
                self.created_campaigns.append(response_data['campaign_id'])
                return True, response_data['campaign_id']
            else:
                print("❌ Campaign creation response missing success or campaign_id")
                return False, None
        return False, None
    
    def test_list_campaigns(self):
        """Test listing all campaigns"""
        success, response = self.run_test(
            "List Campaigns",
            "GET",
            "/api/campaigns",
            200
        )
        
        if success:
            data = response.json()
            if "campaigns" in data and "total" in data:
                print(f"✅ Retrieved {data['total']} campaigns")
                return True
            else:
                print("❌ Campaign list response format incorrect")
                return False
        return False
    
    def test_get_campaign(self, campaign_id):
        """Test getting a specific campaign"""
        success, response = self.run_test(
            f"Get Campaign {campaign_id}",
            "GET",
            f"/api/campaigns/{campaign_id}",
            200
        )
        
        if success:
            data = response.json()
            if "id" in data and data["id"] == campaign_id:
                print(f"✅ Retrieved campaign {campaign_id}")
                return True
            else:
                print("❌ Campaign retrieval response format incorrect")
                return False
        return False
    
    def test_prepare_campaign(self, campaign_id):
        """Test preparing a campaign for sending"""
        success, response = self.run_test(
            f"Prepare Campaign {campaign_id}",
            "POST",
            f"/api/campaigns/{campaign_id}/prepare",
            200
        )
        
        if success:
            data = response.json()
            if data.get("success"):
                print(f"✅ Campaign {campaign_id} prepared successfully")
                return True
            else:
                print(f"❌ Campaign preparation failed: {data.get('message', 'No error message')}")
                return False
        return False
    
    def test_send_campaign(self, campaign_id):
        """Test sending a campaign"""
        success, response = self.run_test(
            f"Send Campaign {campaign_id}",
            "POST",
            f"/api/campaigns/{campaign_id}/send",
            200
        )
        
        if success:
            data = response.json()
            if data.get("success"):
                print(f"✅ Campaign {campaign_id} sent successfully")
                return True
            else:
                print(f"❌ Campaign sending failed: {data.get('message', 'No error message')}")
                return False
        return False
    
    # Contact Management API Tests
    def test_create_contact(self, email, first_name, last_name, company):
        """Test creating a new contact"""
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "company": company,
            "tags": ["test", "api"]
        }
        
        success, response = self.run_test(
            f"Create Contact {email}",
            "POST",
            "/api/contacts",
            200,
            data=data
        )
        
        if success:
            data = response.json()
            if data.get("success") and data.get("contact_id"):
                print(f"✅ Contact created with ID: {data['contact_id']}")
                self.created_contacts.append(data['contact_id'])
                return True, data['contact_id']
            else:
                print("❌ Contact creation response missing success or contact_id")
                return False, None
        return False, None
    
    def test_list_contacts(self):
        """Test listing all contacts"""
        success, response = self.run_test(
            "List Contacts",
            "GET",
            "/api/contacts",
            200
        )
        
        if success:
            data = response.json()
            if "contacts" in data and "total" in data:
                print(f"✅ Retrieved {data['total']} contacts")
                return True
            else:
                print("❌ Contact list response format incorrect")
                return False
        return False
    
    def test_bulk_import_contacts(self):
        """Test bulk importing contacts from CSV"""
        # Create a sample CSV file
        csv_data = [
            ["email", "first_name", "last_name", "company", "phone", "tags"],
            ["john.smith@example.com", "John", "Smith", "Example Corp", "555-1234", "sales,lead"],
            ["jane.doe@example.com", "Jane", "Doe", "Test Inc", "555-5678", "marketing,lead"],
            ["bob.jones@example.com", "Bob", "Jones", "Sample LLC", "555-9012", "support"]
        ]
        
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerows(csv_data)
        csv_file.seek(0)
        
        files = {'file': ('contacts.csv', csv_file.getvalue(), 'text/csv')}
        
        success, response = self.run_test(
            "Bulk Import Contacts",
            "POST",
            "/api/contacts/bulk-import",
            200,
            files=files
        )
        
        if success:
            data = response.json()
            if data.get("success") and "created" in data:
                print(f"✅ Imported {data['created']} contacts, skipped {data.get('skipped', 0)}")
                return True
            else:
                print("❌ Bulk import response format incorrect")
                return False
        return False
    
    # Template Management API Tests
    def test_create_template(self, name, subject, html_content):
        """Test creating a new email template"""
        data = {
            "name": name,
            "subject": subject,
            "html_content": html_content,
            "text_content": "Plain text version of the template",
            "category": "test"
        }
        
        success, response = self.run_test(
            f"Create Template {name}",
            "POST",
            "/api/templates",
            200,
            data=data
        )
        
        if success:
            data = response.json()
            if data.get("success") and data.get("template_id"):
                print(f"✅ Template created with ID: {data['template_id']}")
                self.created_templates.append(data['template_id'])
                return True, data['template_id']
            else:
                print("❌ Template creation response missing success or template_id")
                return False, None
        return False, None
    
    def test_list_templates(self):
        """Test listing all templates"""
        success, response = self.run_test(
            "List Templates",
            "GET",
            "/api/templates",
            200
        )
        
        if success:
            data = response.json()
            if "templates" in data and "total" in data:
                print(f"✅ Retrieved {data['total']} templates")
                return True
            else:
                print("❌ Template list response format incorrect")
                return False
        return False
    
    def test_preview_template(self, template_id):
        """Test previewing a template with sample data"""
        success, response = self.run_test(
            f"Preview Template {template_id}",
            "POST",
            f"/api/templates/{template_id}/preview",
            200
        )
        
        if success:
            data = response.json()
            if "subject" in data and "html_content" in data:
                print(f"✅ Template preview generated successfully")
                return True
            else:
                print("❌ Template preview response format incorrect")
                return False
        return False
    
    # Analytics API Tests
    def test_dashboard_analytics(self):
        """Test getting dashboard analytics"""
        success, response = self.run_test(
            "Dashboard Analytics",
            "GET",
            "/api/analytics/dashboard",
            200
        )
        
        if success:
            data = response.json()
            expected_fields = ["total_contacts", "active_contacts", "total_campaigns", 
                              "total_emails_sent", "total_opens", "total_clicks"]
            
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Dashboard analytics retrieved successfully")
                return True
            else:
                print(f"❌ Dashboard analytics missing fields: {', '.join(missing_fields)}")
                return False
        return False
    
    def test_campaign_analytics(self):
        """Test getting campaign analytics"""
        success, response = self.run_test(
            "Campaign Analytics",
            "GET",
            "/api/analytics/campaigns",
            200
        )
        
        if success:
            data = response.json()
            expected_fields = ["total_campaigns", "total_sent", "total_opens", 
                              "total_clicks", "overall_open_rate", "overall_click_rate"]
            
            missing_fields = [field for field in expected_fields if field not in data]
            
            if not missing_fields:
                print(f"✅ Campaign analytics retrieved successfully")
                return True
            else:
                print(f"❌ Campaign analytics missing fields: {', '.join(missing_fields)}")
                return False
        return False
    
    # Email Personalization API Tests
    def test_validate_personalization(self, content):
        """Test validating content for personalization"""
        data = content  # Send content directly as the request body
        
        success, response = self.run_test(
            "Validate Personalization",
            "POST",
            "/api/personalization/validate?content=" + content,
            200
        )
        
        if success:
            data = response.json()
            if "valid" in data and "variables" in data:
                print(f"✅ Personalization validation successful")
                print(f"  - Valid: {data['valid']}")
                print(f"  - Variables: {', '.join(data.get('variables', []))}")
                return True
            else:
                print("❌ Personalization validation response format incorrect")
                return False
        return False
    
    def test_preview_personalization(self, content):
        """Test previewing personalized content"""
        success, response = self.run_test(
            "Preview Personalization",
            "POST",
            "/api/personalization/preview?content=" + content,
            200
        )
        
        if success:
            data = response.json()
            if "original" in data and "personalized" in data and "variables" in data:
                print(f"✅ Personalization preview successful")
                print(f"  - Original: {data['original']}")
                print(f"  - Personalized: {data['personalized']}")
                return True
            else:
                print("❌ Personalization preview response format incorrect")
                return False
        return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['name']}: {result['status']} - {result['details']}")
        
        return self.tests_passed == self.tests_run

def generate_random_string(length=10):
    """Generate a random string for testing"""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def main():
    print("="*50)
    print("🧪 COLD EMAIL CAMPAIGN SYSTEM API TESTING")
    print("="*50)
    
    tester = EmailServiceTester()
    
    # 1. Test health endpoint
    print("\n🔍 TESTING HEALTH ENDPOINT")
    health_check_result = tester.test_health_endpoint()
    
    # 2. Test legacy APIs for compatibility
    print("\n🔍 TESTING LEGACY EMAIL APIS")
    mx_lookup_gmail = tester.test_mx_lookup("gmail.com")
    email_send_test = tester.test_send_email(
        "test@example.com",
        "test@pixelrisewebco.com",
        "Test User",
        "Test Email",
        "This is a test email from the cold email campaign system.",
        expected_success=False
    )
    
    # 3. Test Authentication & DNS APIs
    print("\n🔍 TESTING AUTHENTICATION & DNS APIS")
    auth_check = tester.test_auth_check("pixelrisewebco.com")
    dns_records = tester.test_dns_records("pixelrisewebco.com")
    
    # 4. Test Contact Management APIs
    print("\n🔍 TESTING CONTACT MANAGEMENT APIS")
    
    # Create individual contacts
    contact1_success, contact1_id = tester.test_create_contact(
        "john.doe@example.com",
        "John",
        "Doe",
        "Example Corp"
    )
    
    contact2_success, contact2_id = tester.test_create_contact(
        "jane.smith@example.com",
        "Jane",
        "Smith",
        "Test Inc"
    )
    
    # List contacts
    list_contacts = tester.test_list_contacts()
    
    # Bulk import contacts
    bulk_import = tester.test_bulk_import_contacts()
    
    # 5. Test Template Management APIs
    print("\n🔍 TESTING TEMPLATE MANAGEMENT APIS")
    
    # Create template with personalization variables
    template_html = """
    <html>
    <body>
        <h1>Hello {{first_name}},</h1>
        <p>We noticed that {{company}} might be interested in our services.</p>
        <p>Would you be available for a quick call this week?</p>
        <p>Best regards,<br>Sales Team</p>
    </body>
    </html>
    """
    
    template_success, template_id = tester.test_create_template(
        "Sales Outreach Template",
        "{{first_name}}, let's connect",
        template_html
    )
    
    # List templates
    list_templates = tester.test_list_templates()
    
    # Preview template
    if template_success:
        preview_template = tester.test_preview_template(template_id)
    
    # 6. Test Email Personalization APIs
    print("\n🔍 TESTING EMAIL PERSONALIZATION APIS")
    
    personalization_content = "Hello {{first_name}} from {{company}}, this is a test email."
    validate_personalization = tester.test_validate_personalization(personalization_content)
    preview_personalization = tester.test_preview_personalization(personalization_content)
    
    # 7. Test Campaign Management APIs
    print("\n🔍 TESTING CAMPAIGN MANAGEMENT APIS")
    
    # Create campaign
    campaign_html = """
    <html>
    <body>
        <h1>Hello {{first_name}},</h1>
        <p>We're reaching out from PixelRise WebCo to introduce our new services.</p>
        <p>As {{company}} is a leader in your industry, we thought you might be interested.</p>
        <p>Best regards,<br>PixelRise Team</p>
    </body>
    </html>
    """
    
    campaign_success, campaign_id = tester.test_create_campaign(
        "Test Outreach Campaign",
        "New services for {{company}}",
        campaign_html,
        "sales@pixelrisewebco.com",
        "PixelRise Sales"
    )
    
    # List campaigns
    list_campaigns = tester.test_list_campaigns()
    
    # Get specific campaign
    if campaign_success:
        get_campaign = tester.test_get_campaign(campaign_id)
        
        # Prepare campaign
        prepare_campaign = tester.test_prepare_campaign(campaign_id)
        
        # Send campaign
        if prepare_campaign:
            send_campaign = tester.test_send_campaign(campaign_id)
    
    # 8. Test Analytics APIs
    print("\n🔍 TESTING ANALYTICS APIS")
    
    dashboard_analytics = tester.test_dashboard_analytics()
    campaign_analytics = tester.test_campaign_analytics()
    
    # Print summary
    success = tester.print_summary()
    
    # Return results for each API category
    results = {
        "health_check": health_check_result,
        "legacy_apis": all([mx_lookup_gmail, email_send_test]),
        "auth_dns_apis": all([auth_check, dns_records]),
        "contact_management": all([contact1_success, contact2_success, list_contacts, bulk_import]),
        "template_management": all([template_success, list_templates]),
        "email_personalization": all([validate_personalization, preview_personalization]),
        "campaign_management": campaign_success and list_campaigns,
        "analytics": all([dashboard_analytics, campaign_analytics])
    }
    
    print("\n" + "="*50)
    print("📊 API CATEGORY RESULTS:")
    print("="*50)
    
    for category, result in results.items():
        status_icon = "✅" if result else "❌"
        print(f"{status_icon} {category.replace('_', ' ').title()}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())