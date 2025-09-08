import requests
import json

# Test the backend API
BASE_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print("Health Check:", response.json())
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_upload(pdf_path):
    """Test PDF upload endpoint"""
    try:
        with open(pdf_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(f"{BASE_URL}/upload", files=files)
            
        print("Upload Response Status:", response.status_code)
        print("Upload Response:", json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Upload test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Backend API...")
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint:")
    health_ok = test_health()
    
    if health_ok:
        print("\n2. Testing PDF Upload:")
        # Test with your existing PDF
        test_upload("papg-draft-escrow-agreement.pdf")
    else:
        print("❌ Backend is not running. Start it with: python app.py")
