from flask import Flask, request, jsonify
from flask_cors import CORS
import fitz
import json
import google.generativeai as genai
from collections import defaultdict
import os
from werkzeug.utils import secure_filename
import tempfile

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure Gemini (you'll need to set your API key)
try:
    from google_api import API_KEY
    if API_KEY and API_KEY != "your-actual-api-key-here":
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-pro")
    else:
        raise ValueError("API key not configured")
except (ImportError, ValueError):
    # If google_api.py doesn't exist or API key not set, use environment variable
    API_KEY = os.getenv('GEMINI_API_KEY')
    if API_KEY:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel("gemini-pro")
    else:
        print("Warning: No Gemini API key found. Please:")
        print("1. Set your API key in google_api.py, OR")
        print("2. Set GEMINI_API_KEY environment variable")
        model = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pages(pdf_path, max_pages=10):
    """Extract text from PDF pages"""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            break
        pages.append(page.get_text())
    doc.close()
    return pages

def analyze_page(page_text, page_num):
    """Analyze page content with Gemini"""
    if model is None:
        return {
            "error": "Gemini API not configured",
            "party_names": ["API Key Required"],
            "dates": ["API Key Required"],
            "amounts": ["API Key Required"],
            "clauses_summary": ["Please configure your Gemini API key"]
        }
    
    prompt = f"""
    You are an AI that extracts structured data from financial agreements.

    Input (financial agreement, page {page_num}):
    {page_text}

    Output:
    Return JSON only with keys:
    - party_names: array of party names found
    - dates: array of dates found
    - amounts: array of monetary amounts found
    - clauses_summary: array of key clauses or terms
    
    Make sure to return valid JSON format only.
    """
    try:
        response = model.generate_content(prompt)
        result = response.text.strip()
        # Clean up the response
        result = result.replace("```json", "").replace("```", "").strip()
        return json.loads(result)
    except Exception as e:
        return {
            "error": f"Failed to analyze page {page_num}: {str(e)}",
            "party_names": [],
            "dates": [],
            "amounts": [],
            "clauses_summary": []
        }

def merge_results(page_results):
    """Merge results from all pages"""
    final = defaultdict(list)

    for page in page_results:
        if isinstance(page, dict):
            # Party Names
            if "party_names" in page and isinstance(page["party_names"], list):
                for p in page["party_names"]:
                    if p and p not in final["party_names"]:
                        final["party_names"].append(p)

            # Dates
            if "dates" in page and isinstance(page["dates"], list):
                for d in page["dates"]:
                    if d and d not in final["dates"]:
                        final["dates"].append(d)

            # Amounts
            if "amounts" in page and isinstance(page["amounts"], list):
                for a in page["amounts"]:
                    if a and a not in final["amounts"]:
                        final["amounts"].append(a)

            # Clauses
            if "clauses_summary" in page and isinstance(page["clauses_summary"], list):
                for clause in page["clauses_summary"]:
                    if clause and clause not in final["clauses_summary"]:
                        final["clauses_summary"].append(clause)

    return dict(final)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Financial Agreement Validator API is running"})

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload and process PDF file"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            # Extract pages from PDF
            pages = extract_pages(file_path, max_pages=10)
            
            if not pages:
                return jsonify({"error": "Could not extract text from PDF"}), 400

            # Analyze each page
            page_results = []
            for i, page_text in enumerate(pages):
                if page_text.strip():  # Only analyze non-empty pages
                    result = analyze_page(page_text, i + 1)
                    page_results.append(result)

            # Merge results
            merged_data = merge_results(page_results)

            # Clean up uploaded file
            os.remove(file_path)

            return jsonify({
                "success": True,
                "filename": filename,
                "pages_processed": len(page_results),
                "extracted_data": merged_data,
                "page_results": page_results  # Include individual page results
            })

        except Exception as e:
            # Clean up file if processing fails
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
    """Test endpoint to verify API is working"""
    return jsonify({
        "message": "API is working!",
        "endpoints": {
            "health": "/health",
            "upload": "/upload (POST with PDF file)",
            "test": "/test"
        }
    })

if __name__ == '__main__':
    print("Starting Financial Agreement Validator API...")
    print("Upload endpoint: /upload")
    print("Health check: /health")
    # Get port from environment variable for Render deployment
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
