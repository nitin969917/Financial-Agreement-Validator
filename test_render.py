import requests
import json
import time

def test_render_deployment(base_url):
    """Test the Render deployment"""
    print(f"🧪 Testing Render Deployment at: {base_url}")
    print("=" * 50)
    
    # Test 1: Health Check
    print("1. Testing Health Endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=30)
        if response.status_code == 200:
            print("✅ Health Check Passed")
            print("Response:", response.json())
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False
    
    # Test 2: Test Endpoint
    print("\n2. Testing API Endpoints...")
    try:
        response = requests.get(f"{base_url}/test", timeout=30)
        if response.status_code == 200:
            print("✅ Test Endpoint Passed")
            print("Response:", response.json())
        else:
            print(f"⚠️ Test Endpoint Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Test Endpoint Error: {e}")
    
    # Test 3: Upload endpoint (without file, just to check if it responds)
    print("\n3. Testing Upload Endpoint (structure)...")
    try:
        response = requests.post(f"{base_url}/upload", timeout=30)
        if response.status_code == 400:  # Expected - no file provided
            print("✅ Upload Endpoint is responding (400 expected without file)")
            print("Response:", response.json())
        else:
            print(f"⚠️ Upload Endpoint Status: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Upload Endpoint Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Deployment test completed!")
    return True

if __name__ == "__main__":
    # Replace this URL with your actual Render URL after deployment
    RENDER_URL = input("Enter your Render app URL (e.g., https://your-app.onrender.com): ").strip()
    
    if not RENDER_URL:
        print("❌ Please provide your Render URL")
        exit(1)
    
    # Remove trailing slash if present
    RENDER_URL = RENDER_URL.rstrip('/')
    
    test_render_deployment(RENDER_URL)
