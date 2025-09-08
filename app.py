from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import json
import os
from werkzeug.utils import secure_filename
import tempfile
import io

app = Flask(__name__)
CORS(app)  # Enable CORS for Flutter app

# Configure upload settings
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pages(pdf_path, max_pages=10):
    """Extract text from PDF pages using PyPDF2"""
    pages = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for i in range(min(max_pages, num_pages)):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                if text.strip():  # Only add non-empty pages
                    pages.append(text)
                    
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return []
    
    return pages

def analyze_page_basic(page_text, page_num):
    """Basic text analysis without AI - extracts some patterns"""
    import re
    
    # Basic extraction patterns
    party_names = []
    dates = []
    amounts = []
    clauses = []
    
    # Find potential party names (capitalized words near "party", "company", etc.)
    party_pattern = r'\b(?:party|company|corporation|llc|inc|ltd)\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)'
    party_matches = re.finditer(party_pattern, page_text, re.IGNORECASE)
    for match in party_matches:
        name = match.group(1).strip()
        if len(name) > 2 and name not in party_names:
            party_names.append(name)
    
    # Find dates
    date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
    date_matches = re.finditer(date_pattern, page_text, re.IGNORECASE)
    for match in date_matches:
        date = match.group().strip()
        if date not in dates:
            dates.append(date)
    
    # Find amounts (money)
    amount_pattern = r'\$[\d,]+\.?\d*|\b\d+,?\d*\s*(?:dollars?|usd)\b'
    amount_matches = re.finditer(amount_pattern, page_text, re.IGNORECASE)
    for match in amount_matches:
        amount = match.group().strip()
        if amount not in amounts:
            amounts.append(amount)
    
    # Find potential clauses (sentences with legal terms)
    legal_terms = ['agreement', 'contract', 'clause', 'term', 'condition', 'obligation', 'payment', 'termination']
    sentences = page_text.split('.')
    for sentence in sentences:
        for term in legal_terms:
            if term.lower() in sentence.lower() and len(sentence.strip()) > 20:
                clauses.append(sentence.strip()[:100] + "..." if len(sentence) > 100 else sentence.strip())
                break
    
    return {
        "party_names": party_names[:5],  # Limit to 5
        "dates": dates[:5],
        "amounts": amounts[:5],
        "clauses_summary": clauses[:3]
    }

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
                    result = analyze_page_basic(page_text, i + 1)
                    page_results.append(result)

            # Merge results
            merged_data = {
                "party_names": [],
                "dates": [],
                "amounts": [],
                "clauses_summary": []
            }
            
            for page_result in page_results:
                for key in merged_data.keys():
                    if key in page_result:
                        for item in page_result[key]:
                            if item and item not in merged_data[key]:
                                merged_data[key].append(item)

            # Clean up uploaded file
            os.remove(file_path)

            return jsonify({
                "success": True,
                "filename": filename,
                "pages_processed": len(page_results),
                "extracted_data": merged_data,
                "page_results": page_results,
                "note": "Using basic text analysis. For AI-powered analysis, configure Gemini API key."
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
