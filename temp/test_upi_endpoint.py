import requests
import json

def test_payment_endpoint():
    # Login first
    login_url = "http://localhost:5000/login"
    login_data = {
        "email": "organiser@example.com",
        "password": "password123"
    }
    
    session = requests.Session()
    login_response = session.post(login_url, data=login_data)
    
    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        print(login_response.text)
        return
    
    print("Login successful")
    
    # Test the payment endpoint
    payment_url = "http://localhost:5000/api/profile/payment"
    payment_data = {
        "method": "upi",
        "panNumber": "ABCDE1234F",
        "upiDetails": {
            "upiId": "testuser@bankname",
            "name": "Test User"
        }
    }
    
    payment_response = session.post(
        payment_url, 
        data=json.dumps(payment_data),
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"Payment API Response Status: {payment_response.status_code}")
    print(f"Payment API Response Content: {payment_response.text}")
    
    # Check profile to see if UPI ID was saved
    profile_url = "http://localhost:5000/api/profile"
    profile_response = session.get(profile_url)
    
    print(f"Profile API Response Status: {profile_response.status_code}")
    print(f"Profile API Response Content: {profile_response.text}")
    
    # Parse the profile response to check UPI ID
    profile_data = profile_response.json()
    if profile_data.get('success') and 'profile' in profile_data:
        payment_info = profile_data['profile'].get('paymentInfo', {})
        upi_details = payment_info.get('upiDetails', {})
        upi_id = upi_details.get('upiId')
        
        print(f"Retrieved UPI ID from profile: {upi_id}")
        if upi_id == "testuser@bankname":
            print("TEST PASSED: UPI ID was successfully saved to the database!")
        else:
            print(f"TEST FAILED: UPI ID doesn't match. Expected 'testuser@bankname', got '{upi_id}'")
    else:
        print("Failed to retrieve profile data")

if __name__ == "__main__":
    test_payment_endpoint()
