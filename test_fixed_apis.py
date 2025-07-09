import requests
import json
import sys
import uuid
from datetime import datetime

BASE_URL = "https://95f130cc-f3a5-499b-b546-b68b3833d046.preview.emergentagent.com"

def test_api(name, method, endpoint, expected_status=200, data=None, params=None, files=None):
    """Test an API endpoint and return the result"""
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'} if not files else {}
    
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
            print(f"Raw Response: {response.text[:200]}...")
        
        success = response.status_code == expected_status
        if success:
            print(f"✅ Passed - Status: {response.status_code}")
        else:
            print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
        
        return success, response
    
    except Exception as e:
        print(f"❌ Error - {str(e)}")
        return False, None

def create_contact():
    """Create a test contact and return its ID"""
    email = f"test.user.{uuid.uuid4()}@example.com"
    data = {
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "company": "Test Company",
        "tags": ["test", "api"]
    }
    
    success, response = test_api(
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
            return data['contact_id']
    
    return None

def create_template():
    """Create a test template and return its ID"""
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
    
    data = {
        "name": f"Test Template {datetime.now().strftime('%H:%M:%S')}",
        "subject": "{{first_name}}, let's connect",
        "html_content": template_html,
        "text_content": "Plain text version of the template",
        "category": "test"
    }
    
    success, response = test_api(
        "Create Template",
        "POST",
        "/api/templates",
        200,
        data=data
    )
    
    if success:
        data = response.json()
        if data.get("success") and data.get("template_id"):
            print(f"✅ Template created with ID: {data['template_id']}")
            return data['template_id']
    
    return None

def test_get_contact_by_id(contact_id):
    """Test getting a contact by ID"""
    success, response = test_api(
        f"Get Contact {contact_id}",
        "GET",
        f"/api/contacts/{contact_id}",
        200
    )
    
    if success:
        data = response.json()
        if "id" in data and data["id"] == contact_id:
            print(f"✅ Retrieved contact {contact_id}")
            return True
        else:
            print("❌ Contact retrieval response format incorrect")
            return False
    return False

def test_export_contacts(format="csv"):
    """Test exporting contacts"""
    success, response = test_api(
        f"Export Contacts ({format})",
        "GET",
        f"/api/contacts/export?format={format}",
        200
    )
    
    if success:
        content_type = response.headers.get('Content-Type', '')
        content_disposition = response.headers.get('Content-Disposition', '')
        
        if format == "csv" and "text/csv" in content_type:
            print(f"✅ Exported contacts to CSV successfully")
            return True
        elif format == "excel" and "spreadsheetml" in content_type:
            print(f"✅ Exported contacts to Excel successfully")
            return True
        else:
            print(f"❌ Contact export format incorrect: {content_type}")
            return False
    return False

def test_get_template_by_id(template_id):
    """Test getting a template by ID"""
    success, response = test_api(
        f"Get Template {template_id}",
        "GET",
        f"/api/templates/{template_id}",
        200
    )
    
    if success:
        data = response.json()
        if "id" in data and data["id"] == template_id:
            print(f"✅ Retrieved template {template_id}")
            return True
        else:
            print("❌ Template retrieval response format incorrect")
            return False
    return False

def test_personalization_validate():
    """Test personalization validation"""
    content = "Hello {{first_name}} from {{company}}, this is a test email."
    success, response = test_api(
        "Validate Personalization",
        "POST",
        "/api/personalization/validate",
        200,
        data={"content": content}
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

def test_personalization_preview():
    """Test personalization preview"""
    content = "Hello {{first_name}} from {{company}}, this is a test email."
    success, response = test_api(
        "Preview Personalization",
        "POST",
        "/api/personalization/preview",
        200,
        data={"content": content}
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

def test_track_email_click():
    """Test email click tracking"""
    tracking_id = str(uuid.uuid4())
    url = "https://example.com"
    success, response = test_api(
        "Track Email Click",
        "GET",
        f"/api/track/click/{tracking_id}?url={url}",
        302  # Expecting a redirect
    )
    
    if success:
        location = response.headers.get('Location', '')
        if url in location:
            print(f"✅ Email click tracking successful with redirect to {location}")
            return True
        else:
            print(f"❌ Email click tracking redirect incorrect: {location}")
            return False
    return False

def test_unsubscribe():
    """Test unsubscribe functionality"""
    email = f"test-{uuid.uuid4()}@example.com"
    data = {
        "email": email,
        "reason": "Test unsubscribe"
    }
    
    success, response = test_api(
        "Unsubscribe Email",
        "POST",
        "/api/unsubscribe",
        200,
        data=data
    )
    
    if success:
        data = response.json()
        if data.get("success"):
            print(f"✅ Unsubscribe successful for {email}")
            return True
        else:
            print(f"❌ Unsubscribe failed: {data.get('message', 'No error message')}")
            return False
    return False

def main():
    print("="*50)
    print("🧪 TESTING PREVIOUSLY FAILING APIS (NOW FIXED)")
    print("="*50)
    
    results = {}
    
    # 1. Test Contact Management APIs - Get Contact by ID
    print("\n🔍 TESTING CONTACT MANAGEMENT APIS - GET CONTACT BY ID")
    contact_id = create_contact()
    if contact_id:
        results["get_contact_by_id"] = test_get_contact_by_id(contact_id)
    else:
        results["get_contact_by_id"] = False
        print("❌ Could not create contact for testing")
    
    # 2. Test Contact Management APIs - Export Contacts
    print("\n🔍 TESTING CONTACT MANAGEMENT APIS - EXPORT CONTACTS")
    results["export_contacts_csv"] = test_export_contacts("csv")
    results["export_contacts_excel"] = test_export_contacts("excel")
    
    # 3. Test Template Management APIs - Get Template by ID
    print("\n🔍 TESTING TEMPLATE MANAGEMENT APIS - GET TEMPLATE BY ID")
    template_id = create_template()
    if template_id:
        results["get_template_by_id"] = test_get_template_by_id(template_id)
    else:
        results["get_template_by_id"] = False
        print("❌ Could not create template for testing")
    
    # 4. Test Email Personalization APIs
    print("\n🔍 TESTING EMAIL PERSONALIZATION APIS")
    results["personalization_validate"] = test_personalization_validate()
    results["personalization_preview"] = test_personalization_preview()
    
    # 5. Test Tracking APIs - Click Tracking
    print("\n🔍 TESTING TRACKING APIS - CLICK TRACKING")
    results["track_email_click"] = test_track_email_click()
    
    # 6. Test Tracking APIs - Unsubscribe Endpoint
    print("\n🔍 TESTING TRACKING APIS - UNSUBSCRIBE ENDPOINT")
    results["unsubscribe"] = test_unsubscribe()
    
    # Print summary
    print("\n" + "="*50)
    print("📊 PREVIOUSLY FAILING APIS RESULTS:")
    print("="*50)
    
    all_passed = True
    for name, result in results.items():
        status_icon = "✅" if result else "❌"
        formatted_name = name.replace("_", " ").title()
        print(f"{status_icon} {formatted_name}")
        if not result:
            all_passed = False
    
    print("\n" + "="*50)
    print(f"📊 OVERALL RESULT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())