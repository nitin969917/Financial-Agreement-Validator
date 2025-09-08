# Financial Agreement Validator - Backend Setup Guide

## Backend Setup (Flask API)

### 1. Prerequisites
- Python 3.8+ installed
- Gemini API key from Google AI Studio

### 2. Installation
```powershell
# Install required packages
pip install Flask Flask-CORS PyMuPDF google-generativeai

# Or install from requirements.txt
pip install -r requirements.txt
```

### 3. Configure API Key
Edit `google_api.py` and replace `your-actual-api-key-here` with your actual Gemini API key:
```python
API_KEY = "AIzaSyA..."  # Your actual API key
```

### 4. Run Backend
```powershell
python app.py
```

The backend will run on `http://localhost:5000`

### 5. Test Backend
```powershell
python test_api.py
```

## API Endpoints

### Health Check
- **URL**: `GET /health`
- **Response**: Server status

### Upload PDF
- **URL**: `POST /upload`
- **Body**: Form-data with 'file' field containing PDF
- **Response**: Extracted financial data in JSON format

### Example Response:
```json
{
  "success": true,
  "filename": "agreement.pdf",
  "pages_processed": 3,
  "extracted_data": {
    "party_names": ["Company A", "Company B"],
    "dates": ["2025-01-01", "2025-12-31"],
    "amounts": ["$100,000", "$50,000"],
    "clauses_summary": ["Payment terms", "Termination clause"]
  }
}
```

## Flutter Integration

### 1. Create Flutter Project
```bash
flutter create financial_validator_app
cd financial_validator_app
```

### 2. Add Dependencies to pubspec.yaml
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  file_picker: ^6.1.1
```

### 3. Flutter Code Example
```dart
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:file_picker/file_picker.dart';

class ApiService {
  static const String baseUrl = 'http://10.158.33.185:5000';  // Use your IP
  
  static Future<Map<String, dynamic>> uploadPDF(File file) async {
    var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/upload'));
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    
    var response = await request.send();
    var responseData = await response.stream.bytesToString();
    
    return json.decode(responseData);
  }
}
```

## Deploy to Production

### Option 1: Local Network
Your backend is already accessible on your local network at:
- `http://10.158.33.185:5000`

### Option 2: Cloud Deployment
Deploy to platforms like:
- Heroku
- Railway
- Google Cloud Run
- AWS EC2

## Troubleshooting

1. **Port already in use**: Change port in app.py
2. **API key error**: Check google_api.py configuration
3. **CORS issues**: Flask-CORS is already configured
4. **Large files**: Increase MAX_CONTENT_LENGTH in app.py
