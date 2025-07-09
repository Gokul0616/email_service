import requests
import json
import sys
import time
import random
import string
import uuid

class DomainRegistrationTester:
    def __init__(self, base_url="https://4b3d5e70-b539-470c-93ba-7d7d8fbbb73c.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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

    def test_domain_registration_valid(self):
        """Test domain registration with valid data"""
        # Generate a random domain name to avoid reserved domain issues
        random_domain = f"test{uuid.uuid4().hex[:8]}.com"
        data = {
            "domain": random_domain,
            "years": 1,
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Valid Data",
            "POST",
            "/api/domains/register",
            200,
            data=data
        )
        
        return success, response

    def test_domain_registration_missing_fields(self):
        """Test domain registration with missing required fields"""
        data = {
            "domain": "example.com",
            "years": 1,
            "registrant_info": {
                # Missing first_name
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US"
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Missing Fields",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_invalid_email(self):
        """Test domain registration with invalid email format"""
        data = {
            "domain": "example.com",
            "years": 1,
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "invalid-email",  # Invalid email format
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Invalid Email",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_invalid_phone(self):
        """Test domain registration with invalid phone number"""
        data = {
            "domain": "example.com",
            "years": 1,
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "123",  # Too short
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Invalid Phone",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_invalid_domain(self):
        """Test domain registration with invalid domain format"""
        data = {
            "domain": "invalid-domain",  # Missing TLD
            "years": 1,
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Invalid Domain",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_invalid_years(self):
        """Test domain registration with invalid years value"""
        data = {
            "domain": "example.com",
            "years": 0,  # Invalid years (must be >= 1)
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Invalid Years",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_empty_fields(self):
        """Test domain registration with empty required fields"""
        data = {
            "domain": "example.com",
            "years": 1,
            "registrant_info": {
                "first_name": "",  # Empty first name
                "last_name": "",   # Empty last name
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            }
        }
        
        success, response = self.run_test(
            "Domain Registration - Empty Fields",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_missing_registrant_info(self):
        """Test domain registration with missing registrant_info object"""
        data = {
            "domain": "example.com",
            "years": 1
            # Missing registrant_info
        }
        
        success, response = self.run_test(
            "Domain Registration - Missing Registrant Info",
            "POST",
            "/api/domains/register",
            422,  # Expecting validation error
            data=data
        )
        
        return success, response

    def test_domain_registration_extra_fields(self):
        """Test domain registration with extra unexpected fields"""
        data = {
            "domain": "example.com",
            "years": 1,
            "registrant_info": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "US",
                "organization": "",
                "privacy_protection": True
            },
            "extra_field": "This is an extra field"  # Extra field
        }
        
        success, response = self.run_test(
            "Domain Registration - Extra Fields",
            "POST",
            "/api/domains/register",
            200,  # Should still work with extra fields
            data=data
        )
        
        return success, response

    def test_domain_registration_malformed_json(self):
        """Test domain registration with malformed JSON"""
        # This is a direct request to simulate malformed JSON
        url = f"{self.base_url}/api/domains/register"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing Domain Registration - Malformed JSON...")
        
        try:
            # Send malformed JSON
            response = requests.post(url, data="{ this is not valid json }", headers=headers)
            
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                print(f"Raw Response: {response.text}")
            
            success = response.status_code == 422  # Expecting validation error
            if success:
                self.tests_passed += 1
                result = {"name": "Domain Registration - Malformed JSON", "status": "PASS", "details": "Test passed successfully"}
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                result = {"name": "Domain Registration - Malformed JSON", "status": "FAIL", "details": f"Expected status 422, got {response.status_code}"}
                print(f"❌ Failed - Expected 422, got {response.status_code}")
            
            self.test_results.append(result)
            return success, response
        
        except Exception as e:
            result = {"name": "Domain Registration - Malformed JSON", "status": "ERROR", "details": str(e)}
            self.test_results.append(result)
            print(f"❌ Error - {str(e)}")
            return False, None

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
    print("🧪 DOMAIN REGISTRATION API TESTING")
    print("="*50)
    
    tester = DomainRegistrationTester()
    
    # Test with valid data
    valid_test, valid_response = tester.test_domain_registration_valid()
    
    # Test with invalid data
    missing_fields_test, _ = tester.test_domain_registration_missing_fields()
    invalid_email_test, _ = tester.test_domain_registration_invalid_email()
    invalid_phone_test, _ = tester.test_domain_registration_invalid_phone()
    invalid_domain_test, _ = tester.test_domain_registration_invalid_domain()
    invalid_years_test, _ = tester.test_domain_registration_invalid_years()
    empty_fields_test, _ = tester.test_domain_registration_empty_fields()
    missing_registrant_info_test, _ = tester.test_domain_registration_missing_registrant_info()
    extra_fields_test, _ = tester.test_domain_registration_extra_fields()
    malformed_json_test, _ = tester.test_domain_registration_malformed_json()
    
    # Print summary
    success = tester.print_summary()
    
    # Detailed analysis of 422 errors
    print("\n" + "="*50)
    print("📊 ANALYSIS OF 422 VALIDATION ERRORS:")
    print("="*50)
    
    if not valid_test and valid_response and valid_response.status_code == 422:
        print("❌ Even valid data is causing 422 errors. This suggests a fundamental issue with the API endpoint.")
        try:
            error_detail = valid_response.json().get("detail", "No detailed error message")
            print(f"   Error details: {error_detail}")
        except:
            print("   Could not parse error details from response.")
    
    print("\nThe following conditions trigger 422 validation errors:")
    if missing_fields_test:
        print("✅ Missing required fields (as expected)")
    if invalid_email_test:
        print("✅ Invalid email format (as expected)")
    if invalid_phone_test:
        print("✅ Invalid phone number (as expected)")
    if invalid_domain_test:
        print("✅ Invalid domain format (as expected)")
    if invalid_years_test:
        print("✅ Invalid years value (as expected)")
    if empty_fields_test:
        print("✅ Empty required fields (as expected)")
    if missing_registrant_info_test:
        print("✅ Missing registrant_info object (as expected)")
    if malformed_json_test:
        print("✅ Malformed JSON (as expected)")
    
    print("\nRecommendations:")
    if not valid_test:
        print("1. Fix the domain registration endpoint to properly handle valid data")
        print("2. Check for any discrepancies between the expected request format and the actual implementation")
        print("3. Verify that all required fields are being properly validated")
    else:
        print("The domain registration endpoint is working correctly with valid data.")
        print("422 errors are correctly returned for invalid input as expected.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())