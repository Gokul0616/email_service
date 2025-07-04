import requests
import json
import sys
import time

class EmailServiceTester:
    def __init__(self, base_url="https://abec3ab6-a9db-4d64-8e78-afb5853d77f8.preview.emergentagent.com"):
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

    def test_send_email(self, to_email, from_email, from_name, subject, body):
        """Test sending an email"""
        data = {
            "to_email": to_email,
            "from_email": from_email,
            "from_name": from_name,
            "subject": subject,
            "body": body,
            "is_html": False
        }
        
        success, response = self.run_test(
            "Send Email",
            "POST",
            "/api/send-email",
            200,
            data=data
        )
        
        if success:
            data = response.json()
            if data.get("success") and data.get("message_id"):
                print(f"✅ Email sent successfully with message ID: {data['message_id']}")
                return True
            else:
                print("❌ Email sending response format incorrect")
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

def main():
    print("="*50)
    print("🧪 CUSTOM EMAIL SERVICE API TESTING")
    print("="*50)
    
    tester = EmailServiceTester()
    
    # 1. Test health endpoint
    print("\n🔍 TESTING HEALTH ENDPOINT")
    tester.test_health_endpoint()
    
    # 2. Test MX record lookup for multiple domains
    print("\n🔍 TESTING MX RECORD LOOKUP")
    tester.test_mx_lookup("gmail.com")
    tester.test_mx_lookup("yahoo.com")
    tester.test_mx_lookup("outlook.com")
    
    # 3. Test sending email with the specified test data
    print("\n🔍 TESTING EMAIL SENDING")
    tester.test_send_email(
        "test@gmail.com",
        "test@example.com",
        "Test User",
        "Test from Custom SMTP Client",
        "This is a test email from our custom SMTP implementation."
    )
    
    # Print summary
    success = tester.print_summary()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())