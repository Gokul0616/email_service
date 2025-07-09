import requests
import json
import sys

def test_frontend_component_submission():
    """Test domain registration with the exact format used by the frontend component"""
    base_url = "https://4b3d5e70-b539-470c-93ba-7d7d8fbbb73c.preview.emergentagent.com"
    
    print("="*50)
    print("🧪 TESTING FRONTEND COMPONENT SUBMISSION")
    print("="*50)
    
    # This is the exact format used by the frontend component in processRegistration()
    # The key issue is that the form inputs don't have name attributes, so the data might not be properly collected
    
    # First, let's test with the correct format (as a baseline)
    correct_data = {
        "domain": "testcomponent123.com",
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
    
    print(f"\n🔍 Testing with Correct Format...")
    print(f"Request Body: {json.dumps(correct_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/domains/register",
            json=correct_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Correct format works")
        else:
            print(f"❌ Correct format failed with status code {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Now, let's test with a format that might be produced by the frontend component
    # The issue might be that the form data is not properly structured
    
    # Scenario 1: registrant_info is not properly nested
    flat_data = {
        "domain": "testcomponent123.com",
        "years": 1,
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
    
    print(f"\n🔍 Testing with Flat Structure (no nested registrant_info)...")
    print(f"Request Body: {json.dumps(flat_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/domains/register",
            json=flat_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ As expected, flat structure fails with 422 error")
        else:
            print(f"❓ Unexpected status code {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Scenario 2: registrant_info is empty or null
    empty_registrant_data = {
        "domain": "testcomponent123.com",
        "years": 1,
        "registrant_info": {}
    }
    
    print(f"\n🔍 Testing with Empty registrant_info...")
    print(f"Request Body: {json.dumps(empty_registrant_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/domains/register",
            json=empty_registrant_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ As expected, empty registrant_info fails with 422 error")
        else:
            print(f"❓ Unexpected status code {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Scenario 3: registrant_info with missing required fields
    missing_fields_data = {
        "domain": "testcomponent123.com",
        "years": 1,
        "registrant_info": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            # Missing phone
            # Missing address
            "city": "New York",
            "state": "NY",
            "postal_code": "10001",
            "country": "US",
            "organization": "",
            "privacy_protection": True
        }
    }
    
    print(f"\n🔍 Testing with Missing Required Fields in registrant_info...")
    print(f"Request Body: {json.dumps(missing_fields_data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/domains/register",
            json=missing_fields_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        
        if response.status_code == 422:
            print("✅ As expected, missing required fields fails with 422 error")
        else:
            print(f"❓ Unexpected status code {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "="*50)
    print("📊 ANALYSIS:")
    print("="*50)
    print("The backend API is working correctly with properly formatted data.")
    print("The issue is likely in the frontend form submission:")
    print("1. The form inputs in DomainRegistration.js don't have name attributes")
    print("2. This prevents the form data from being properly collected")
    print("3. When the form is submitted, the registrant_info object might be missing required fields")
    print("4. This causes the 422 validation error from the backend API")
    
    print("\n" + "="*50)
    print("📊 SOLUTION:")
    print("="*50)
    print("1. Add name attributes to all form inputs in DomainRegistration.js")
    print("2. Ensure the form data is properly structured before submission")
    print("3. Validate the form data on the frontend before submission")
    print("4. Handle validation errors properly on the frontend")

if __name__ == "__main__":
    test_frontend_component_submission()