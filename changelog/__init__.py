import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

def get_client():
    from utils.key_manager import key_manager
    key = key_manager.get_next_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.5-flash")

def detect_changes(old_api_info: dict, new_api_info: dict) -> dict:
    """
    Compares two extracted API infos and detects changes.
    Returns structured changelog.
    """
    old_endpoints = {ep["path"]: ep for ep in old_api_info.get("endpoints", [])}
    new_endpoints = {ep["path"]: ep for ep in new_api_info.get("endpoints", [])}

    added = []
    removed = []
    modified = []
    unchanged = []

    # Find added and modified
    for path, ep in new_endpoints.items():
        if path not in old_endpoints:
            added.append(ep)
        else:
            old_ep = old_endpoints[path]
            old_params = {p["name"] for p in old_ep.get("parameters", [])}
            new_params = {p["name"] for p in ep.get("parameters", [])}

            if old_params != new_params or old_ep.get("method") != ep.get("method"):
                modified.append({
                    "path": path,
                    "method": ep["method"],
                    "description": ep.get("description", ""),
                    "added_params": list(new_params - old_params),
                    "removed_params": list(old_params - new_params),
                    "method_changed": old_ep.get("method") != ep.get("method"),
                    "old_method": old_ep.get("method"),
                    "new_method": ep.get("method")
                })
            else:
                unchanged.append(ep)

    # Find removed
    for path, ep in old_endpoints.items():
        if path not in new_endpoints:
            removed.append(ep)

    # Use Gemini to generate a human readable summary
    summary = generate_summary(added, removed, modified, old_api_info, new_api_info)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "summary": summary,
        "stats": {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "unchanged": len(unchanged),
            "total_old": len(old_endpoints),
            "total_new": len(new_endpoints)
        }
    }


def generate_summary(added, removed, modified, old_info, new_info):
    """Uses Gemini to write a human readable changelog summary"""
    prompt = f"""
You are an API changelog analyst. Based on the following API changes, write a concise developer-friendly changelog summary.

API: {old_info.get("api_name", "Unknown API")}

Changes detected:
- {len(added)} endpoint(s) added: {[ep["path"] for ep in added]}
- {len(removed)} endpoint(s) removed: {[ep["path"] for ep in removed]}
- {len(modified)} endpoint(s) modified: {[ep["path"] for ep in modified]}

Write a short 2-3 sentence summary of what changed and what developers should watch out for.
Be direct and technical. No markdown, no bullet points, plain text only.
"""
    for attempt in range(3):
        try:
            response = get_client().generate_content(prompt)
            
            return response.text.strip()
        except Exception as e:
            if "429" in str(e) or "503" in str(e) or "UNAVAILABLE" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = (attempt + 1) * 15
                print(f"Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                return "Could not generate summary."
    return "Could not generate summary."