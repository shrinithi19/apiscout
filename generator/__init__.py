import google.generativeai as genai
from dotenv import load_dotenv
import os
import time

load_dotenv()

def get_client():
    from utils.key_manager import key_manager
    key = key_manager.get_next_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")

def generate_wrapper(api_info: dict) -> str:
    """
    Takes extracted API info and generates a Python wrapper class
    with error handling intelligence.
    """

    endpoints_description = ""
    for ep in api_info.get("endpoints", []):
        params = ", ".join([
            f"{p['name']}: {p['type']}"
            for p in ep.get("parameters", [])
            if p.get("required", False) and p["name"] != api_info.get("authentication", {}).get("parameter_name")
        ])
        endpoints_description += f"- {ep['method']} {ep['path']}: {ep['description']} | Params: {params}\n"

    auth = api_info.get("authentication", {})
    prompt = f"""
You are an expert Python developer. Generate a clean, production-ready Python wrapper class for the following API.

API Details:
- Name: {api_info.get("api_name")}
- Base URL: {api_info.get("base_url")}
- Description: {api_info.get("description")}
- Authentication: {auth.get("type")} using parameter '{auth.get("parameter_name")}' — {auth.get("description")}
- Rate Limits: {api_info.get("rate_limits")}

Endpoints:
{endpoints_description}

Requirements for the generated class:
1. Class name should be based on the API name
2. Constructor should accept the API key and store base URL
3. Each endpoint becomes a method with proper parameters
4. Every method must include:
   - Specific error handling for status codes:
     * 400 → raise ValueError("Bad request: check your parameters")
     * 401 → raise PermissionError("Invalid API key")
     * 404 → raise LookupError("Resource not found")
     * 429 → raise ConnectionAbortedError("Rate limit exceeded, slow down requests")
     * 500 → raise RuntimeError("API server error, try again later")
   - Timeout of 10 seconds on every request
   - Return parsed JSON response
5. Add a usage example in comments at the bottom
6. Use type hints on all methods
7. Add docstrings to every method

Generate ONLY the Python code, no explanation, no markdown backticks.
"""

    for attempt in range(3):
        try:
            response = get_client().generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = (attempt + 1) * 15
                print(f"Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)
            else:
                print(f"Error: {e}")
                return ""

    return ""


def generate_nl_to_api(api_info: dict, user_query: str) -> str:
    """
    Takes a natural language query and generates the exact Python
    code to make that specific API call using the wrapper.
    """
    endpoints_description = ""
    for ep in api_info.get("endpoints", []):
        endpoints_description += f"- {ep['method']} {ep['path']}: {ep['description']}\n"

    prompt = f"""
You are an expert Python developer working with the {api_info.get("api_name")}.

Available endpoints:
{endpoints_description}

User request: "{user_query}"

Based on the user's request, generate ONLY the Python code snippet that:
1. Creates an instance of the wrapper class (assume it's already imported as the class name)
2. Calls the correct method with appropriate parameters
3. Prints or returns the result
4. Includes a comment explaining what the code does

Use placeholder values like "your_api_key", "your_city" where real values are needed.
Generate ONLY the Python code, no explanation, no markdown backticks.
"""

    for attempt in range(3):
        try:
            response = get_client().models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text.strip()

        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = (attempt + 1) * 15
                print(f"Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)
            else:
                print(f"Error: {e}")
                return ""

    return ""


if __name__ == "__main__":
    import sys
    import json
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from scraper import scrape_docs
    from embedder import store_in_chromadb, query_collection
    from extractor import extract_api_info

    print("Scraping docs...")
    pages = scrape_docs("https://openweathermap.org/api", max_pages=5)

    print("Embedding chunks...")
    collection = store_in_chromadb(pages)

    print("Querying relevant chunks...")
    chunks = query_collection(collection, "API endpoints authentication base URL parameters", n_results=8)

    print("Extracting API info...")
    api_info = extract_api_info(chunks)

    print("Generating Python wrapper...")
    wrapper_code = generate_wrapper(api_info)
    print("\n--- Generated Wrapper ---")
    print(wrapper_code)

    print("\n--- Natural Language to API Call ---")
    nl_code = generate_nl_to_api(api_info, "get me the current weather for Chennai")
    print(nl_code)