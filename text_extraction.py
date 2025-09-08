import fitz
import json
import google.generativeai as genai
from collections import defaultdict
from google_api import API_KEY

# Step 1: Configure Gemini
genai.configure(api_key="AIzaSyAp1DL41t1IF9Com-Vrl8-ivh2A-xSF_I4")
model = genai.GenerativeModel("gemini-2.0-flash")

# Step 2: Extract page-wise text
def extract_pages(pdf_path, max_pages=3):
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        if i >= max_pages:  # sirf test ke liye 3 pages
            break
        pages.append(page.get_text())
    return pages

# Step 3: Analyze each page with Gemini
def analyze_page(page_text, page_num):
    prompt = f"""
    You are an AI that extracts structured data from financial agreements.

    Input (financial agreement, page {page_num}):
    {page_text}

    Output:
    Return JSON only with keys:
    - party_names
    - dates
    - amounts
    - clauses_summary
    """
    response = model.generate_content(prompt)
    return response.text.strip()

def merge_results(page_results):
    final = defaultdict(list)

    for page in page_results:
        # Party Names
        if "party_names" in page:
            for p in page["party_names"]:
                if p not in final["party_names"]:
                    final["party_names"].append(p)

        # Dates
        if "dates" in page:
            for d in page["dates"]:
                if d not in final["dates"]:
                    final["dates"].append(d)

        # Amounts
        if "amounts" in page:
            for a in page["amounts"]:
                if a not in final["amounts"]:
                    final["amounts"].append(a)

        # Clauses (can be string OR dict)
        if "clauses_summary" in page:
            for clause in page["clauses_summary"]:
                if clause not in final["clauses_summary"]:
                    final["clauses_summary"].append(clause)

    return dict(final)

# Step 4: Run test
if __name__ == "__main__":
    pages = extract_pages("papg-draft-escrow-agreement.pdf", max_pages=3)

    results = []
    for i, page_text in enumerate(pages):
        print(f"\n🔹 Analyzing page {i+1}...\n")
        print(f"\n Page text :{page_text}\n\n")
        try:
            result = analyze_page(page_text, i + 1)
            result = result.replace("`", "").replace("json", "")
            print(result)
            results.append(json.loads(result))  # try parse JSON
        except Exception as e:
            print("⚠️ Error parsing JSON:", e)
            results.append({"page": i + 1, "raw_output": result})

    print("\n✅ Final Extracted Data:")
    print(json.dumps(results, indent=2))

    merged = merge_results(results)
    print("\n✅ Merged JSON:")
    print(json.dumps(merged, indent=2))
