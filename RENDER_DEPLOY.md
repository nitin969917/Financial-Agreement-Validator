# Render Deployment Guide for Financial Agreement Validator

## Step-by-Step Render Deployment

### 1. Prepare Your Repository

Make sure you have these files in your repository:
- ✅ `app.py` (main Flask application)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `Procfile` (tells Render how to run your app)
- ✅ `runtime.txt` (specifies Python version)
- ✅ `google_api.py` (API key configuration - optional for local)

### 2. Push to GitHub

```bash
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### 3. Deploy on Render

1. **Go to Render**: https://render.com
2. **Sign up/Login** with your GitHub account
3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `Financial-Agreement-Validator`
   - Select the repository

4. **Configure the Service**:
   - **Name**: `financial-agreement-validator`
   - **Region**: Choose closest to you
   - **Branch**: `main` or `master`
   - **Root Directory**: Leave empty (or `.` if needed)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

5. **Environment Variables**:
   Click "Environment" and add:
   - **Key**: `GEMINI_API_KEY`
   - **Value**: Your actual Gemini API key (e.g., `AIzaSyA...`)

6. **Advanced Settings**:
   - **Instance Type**: Free tier
   - **Auto Deploy**: Yes (recommended)

7. **Click "Create Web Service"**

### 4. Wait for Deployment

- Render will build and deploy your app (takes 2-5 minutes)
- You'll get a URL like: `https://financial-agreement-validator.onrender.com`

### 5. Test Your Deployed App

Use the test script below to verify it's working.

## Test Your Deployment

Save this as `test_render.py`:

```python
import requests
import json

# Replace with your Render URL
BASE_URL = "https://financial-agreement-validator.onrender.com"

def test_deployment():
    print("🧪 Testing Render Deployment...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        print("✅ Health Check Response:", response.json())
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    test_deployment()
```

## Common Issues & Solutions

### 1. Build Fails
- Check `requirements.txt` for correct package versions
- Ensure `runtime.txt` has supported Python version

### 2. App Crashes
- Check logs in Render dashboard
- Verify environment variables are set
- Make sure `Procfile` is correct

### 3. API Key Issues
- Set `GEMINI_API_KEY` in Render environment variables
- Don't commit your actual API key to GitHub

### 4. Timeout Issues
- Render free tier has cold start delays
- First request might take 30+ seconds

## Your Render URLs

After deployment, your endpoints will be:
- **Health Check**: `https://your-app-name.onrender.com/health`
- **Upload PDF**: `https://your-app-name.onrender.com/upload`

## Flutter Integration

Update your Flutter app's base URL to:
```dart
static const String baseUrl = 'https://your-app-name.onrender.com';
```

## Monitoring

- **Render Dashboard**: Monitor logs, metrics, and deployments
- **Uptime**: Free tier sleeps after 15 minutes of inactivity
- **Logs**: Check for errors and debug issues
