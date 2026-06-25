import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

def get_client():
    from utils.key_manager import key_manager
    key = key_manager.get_next_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")

def extract_api_info(chunks: list[str]) -> dict:
    """
    Sends relevant chunks to Gemini and extracts structured API information.
    """
    combined_text = "\n\n".join(chunks)

    prompt = f"""
You are an expert API analyst. Analyze the following API documentation text and extract structured information.

Documentation Text:
{combined_text}

Extract and return ONLY a valid JSON object with this exact structure:
{{
    "api_name": "Name of the API",
    "base_url": "Base URL of the API",
    "description": "Brief description of what this API does",
    "authentication": {{
        "type": "API Key / OAuth2 / Bearer Token / None",
        "description": "How to authenticate",
        "parameter_name": "Name of the auth parameter if applicable"
    }},
    "endpoints": [
        {{
            "method": "GET/POST/PUT/DELETE",
            "path": "/endpoint/path",
            "description": "What this endpoint does",
            "parameters": [
                {{
                    "name": "parameter name",
                    "type": "string/integer/float/boolean",
                    "required": true,
                    "description": "What this parameter does"
                }}
            ]
        }}
    ],
    "rate_limits": "Rate limit information if available or null"
}}

Return ONLY the JSON object, no explanation, no markdown, no extra text.
"""

    for attempt in range(3):
        try:
            response = get_client().generate_content(prompt)
            raw = response.text.strip()

            # Clean up if Gemini wraps in markdown
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            return json.loads(raw)

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = (attempt + 1) * 15
                print(f"Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)
            else:
                print(f"Error: {e}")
                return {}

    print("Failed after 3 attempts.")
    return {}


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from scraper import scrape_docs
    from embedder import store_in_chromadb, query_collection

    print("Scraping docs...")
    pages = scrape_docs("https://openweathermap.org/api", max_pages=5)

    print("Embedding chunks...")
    collection = store_in_chromadb(pages)

    print("Querying relevant chunks...")
    chunks = query_collection(collection, "API endpoints authentication base URL parameters", n_results=8)

    print("Extracting API info with Gemini...")
    api_info = extract_api_info(chunks)

    print("\n--- Extracted API Info ---")
    print(json.dumps(api_info, indent=2))