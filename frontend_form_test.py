import requests
import json
import sys

def test_frontend_form_submission():
    """Test domain registration with the exact format used by the frontend"""
    base_url = "https://4b3d5e70-b539-470c-93ba-7d7d8fbbb73c.preview.emergentagent.com"
    
    print("="*50)
    print("🧪 TESTING FRONTEND FORM SUBMISSION")
    print("="*50)
    
    # This is the exact format used by the frontend in processRegistration()
    data = {
        "domain": "testfrontend123.com",
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
    
    print(f"\n🔍 Testing Domain Registration with Frontend Format...")
    print(f"Request Body: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(
            f"{base_url}/api/domains/register",
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except:
            print(f"Raw Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Frontend form submission works correctly")
            return True
        else:
            print(f"❌ Frontend form submission failed with status code {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_frontend_form_submission()