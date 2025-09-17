from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
import json
import os
from werkzeug.utils import secure_filename
import tempfile
import io
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from gemini_api_key import API_KEY  # Import the API key from the separate file
app = Flask(__name__)
CORS(app)

# Configure Gemini AI
GEMINI_API_KEY = API_KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_pages(pdf_path, max_pages=10):
    pages = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for i in range(min(max_pages, num_pages)):
                page = pdf_reader.pages[i]
                text = page.extract_text()
                if text.strip():
                    pages.append(text)
                    
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return []
    
    return pages

def analyze_with_gemini(text_content):
    if not GEMINI_API_KEY:
        raise Exception("Gemini API key not configured")

    prompt = """
    Analyze this financial agreement text and provide a detailed JSON response with the following information:
    1. All party names mentioned in the agreement
    2. Important dates including signing date, effective date, termination date
    3. All monetary amounts mentioned
    4. Key clauses and their summaries
    5. Agreement type and purpose
    6. Risks and important considerations
    7. Validation status (valid/invalid) with reasons

    Text to analyze:
    {text}
    
    Provide the response in a structured JSON format.
    """.format(text=text_content)

    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40
            },
            safety_settings=[
                {
                    "category": HarmCategory.HARASSMENT,
                    "threshold": HarmBlockThreshold.MEDIUM_AND_ABOVE
                },
                {
                    "category": HarmCategory.HATE_SPEECH,
                    "threshold": HarmBlockThreshold.MEDIUM_AND_ABOVE
                }
            ]
        )
        
        # Parse the response text as JSON
        analysis_result = json.loads(response.text)
        return analysis_result
    except Exception as e:
        print(f"Error in Gemini analysis: {str(e)}")
        return None

def analyze_page_basic(page_text, page_num):
    import re
    
    party_names = []
    dates = []
    amounts = []
    clauses = []
    
    party_pattern = r'\b(?:party|company|corporation|llc|inc|ltd)\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)'
    party_matches = re.finditer(party_pattern, page_text, re.IGNORECASE)
    for match in party_matches:
        name = match.group(1).strip()
        if len(name) > 2 and name not in party_names:
            party_names.append(name)
    
    date_pattern = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
    date_matches = re.finditer(date_pattern, page_text, re.IGNORECASE)
    for match in date_matches:
        date = match.group().strip()
        if date not in dates:
            dates.append(date)
    
    amount_pattern = r'\$[\d,]+\.?\d*|\b\d+,?\d*\s*(?:dollars?|usd)\b'
    amount_matches = re.finditer(amount_pattern, page_text, re.IGNORECASE)
    for match in amount_matches:
        amount = match.group().strip()
        if amount not in amounts:
            amounts.append(amount)
    
    legal_terms = ['agreement', 'contract', 'clause', 'term', 'condition', 'obligation', 'payment', 'termination']
    sentences = page_text.split('.')
    for sentence in sentences:
        for term in legal_terms:
            if term.lower() in sentence.lower() and len(sentence.strip()) > 20:
                clauses.append(sentence.strip()[:100] + "..." if len(sentence) > 100 else sentence.strip())
                break
    
    return {
        "party_names": party_names[:5],
        "dates": dates[:5],
        "amounts": amounts[:5],
        "clauses_summary": clauses[:3]
    }

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "Financial Agreement Validator API is running"})

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            pages = extract_pages(file_path, max_pages=10)
            
            if not pages:
                return jsonify({"error": "Could not extract text from PDF"}), 400

            # Combine all pages into one text for comprehensive analysis
            full_text = "\n\n".join(pages)

            # First do basic extraction for backup
            basic_results = []
            for i, page_text in enumerate(pages):
                if page_text.strip():
                    result = analyze_page_basic(page_text, i + 1)
                    basic_results.append(result)

            # Use Gemini API for advanced analysis if available
            gemini_analysis = None
            if GEMINI_API_KEY:
                try:
                    gemini_analysis = analyze_with_gemini(full_text)
                except Exception as e:
                    print(f"Gemini analysis failed: {str(e)}")

            # Clean up the uploaded file
            os.remove(file_path)

            # Prepare the response
            response_data = {
                "success": True,
                "filename": filename,
                "pages_processed": len(pages)
            }

            if gemini_analysis:
                response_data["ai_analysis"] = gemini_analysis
                response_data["analysis_type"] = "ai_powered"
            else:
                # Fallback to basic analysis
                merged_data = {
                    "party_names": [],
                    "dates": [],
                    "amounts": [],
                    "clauses_summary": []
                }
                
                for page_result in basic_results:
                    for key in merged_data.keys():
                        if key in page_result:
                            for item in page_result[key]:
                                if item and item not in merged_data[key]:
                                    merged_data[key].append(item)
                
                response_data["extracted_data"] = merged_data
                response_data["page_results"] = basic_results
                response_data["analysis_type"] = "basic"
                if GEMINI_API_KEY:
                    response_data["note"] = "AI analysis failed, falling back to basic analysis"
                else:
                    response_data["note"] = "Using basic analysis. For AI-powered analysis, configure Gemini API key"

            return jsonify(response_data)

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
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
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
