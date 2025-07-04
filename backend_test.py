import requests
import json
import sys
import time
import random
import string

class EmailServiceTester:
    def __init__(self, base_url="https://a5842474-a2d4-4669-8481-38e27e7f34ba.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            
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
            if data.get("status") == "healthy" and data.get("service") == "custom-email-server":
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
    print("🧪 CUSTOM EMAIL SERVICE API TESTING")
    print("="*50)
    
    tester = EmailServiceTester()
    
    # 1. Test health endpoint
    print("\n🔍 TESTING HEALTH ENDPOINT")
    health_check_result = tester.test_health_endpoint()
    
    # 2. Test MX record lookup for multiple domains
    print("\n🔍 TESTING MX RECORD LOOKUP")
    mx_lookup_gmail = tester.test_mx_lookup("gmail.com")
    mx_lookup_yahoo = tester.test_mx_lookup("yahoo.com")
    mx_lookup_nonexistent = tester.test_mx_lookup_nonexistent(f"{generate_random_string()}.invalid")
    
    # 3. Test sending email with various scenarios
    print("\n🔍 TESTING EMAIL SENDING")
    
    # Test with non-existent account
    email_send_nonexistent = tester.test_send_email(
        "test@gmail.com",
        "test@example.com",
        "Test User",
        "Test to Non-existent Account",
        "This is a test to a non-existent account.",
        expected_success=False,
        error_check="may not exist"
    )
    
    # Test with invalid email format
    invalid_email_format = tester.test_invalid_email_format()
    
    # Test with valid format but likely to fail
    email_send_valid_format = tester.test_send_email(
        "test@example.com",  # example.com might not accept emails
        "test@example.com",
        "Test User",
        "Test with Valid Format",
        "This is a test with valid format but likely to fail.",
        expected_success=False
    )
    
    # 4. Test received emails API
    print("\n🔍 TESTING RECEIVED EMAILS API")
    received_emails = tester.test_received_emails()
    
    # 5. Test user emails API
    print("\n🔍 TESTING USER EMAILS API")
    user_emails = tester.test_user_emails("test@example.com")
    user_emails_sent = tester.test_user_emails("test@example.com", "sent")
    
    # 6. Test server status API
    print("\n🔍 TESTING SERVER STATUS API")
    server_status = tester.test_server_status()
    
    # 7. Test DNS records API
    print("\n🔍 TESTING DNS RECORDS API")
    dns_records = tester.test_dns_records("example.com")
    
    # Print summary
    success = tester.print_summary()
    
    # Return results for each API category
    results = {
        "health_check": health_check_result,
        "mx_lookup": all([mx_lookup_gmail, mx_lookup_yahoo, mx_lookup_nonexistent]),
        "email_sending": all([email_send_nonexistent, invalid_email_format, email_send_valid_format]),
        "received_emails": received_emails,
        "user_emails": all([user_emails, user_emails_sent]),
        "server_status": server_status,
        "dns_records": dns_records
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