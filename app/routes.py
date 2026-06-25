from flask import Blueprint, request, jsonify, render_template
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import scrape_docs
from embedder import store_in_chromadb, query_collection
from extractor import extract_api_info
from generator import generate_wrapper, generate_nl_to_api
from changelog import detect_changes

bp = Blueprint("main", __name__)
current_api_info = {}

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/scout", methods=["POST"])
def scout():
    global current_api_info
    data = request.get_json()
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        pages = scrape_docs(url, max_pages=8)
        collection = store_in_chromadb(pages)
        chunks = query_collection(collection, "API endpoints authentication base URL parameters", n_results=8)
        api_info = extract_api_info(chunks)
        current_api_info = api_info
        wrapper_code = generate_wrapper(api_info)
        return jsonify({"api_info": api_info, "wrapper_code": wrapper_code, "pages_scraped": len(pages)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/ask", methods=["POST"])
def ask():
    global current_api_info
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"error": "No query provided"}), 400
    if not current_api_info:
        return jsonify({"error": "Please scout an API first"}), 400
    try:
        code = generate_nl_to_api(current_api_info, query)
        return jsonify({"code": code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route("/changelog", methods=["POST"])
def changelog():
    data = request.get_json()
    old_url = data.get("old_url", "").strip()
    new_url = data.get("new_url", "").strip()

    if not old_url or not new_url:
        return jsonify({"error": "Both URLs required"}), 400

    try:
        # Scrape and extract both versions
        print(f"Scraping old: {old_url}")
        old_pages = scrape_docs(old_url, max_pages=8)
        old_collection = store_in_chromadb(old_pages, collection_name="old_api")
        old_chunks = query_collection(old_collection, "API endpoints authentication base URL parameters", n_results=8)
        old_info = extract_api_info(old_chunks)

        print(f"Scraping new: {new_url}")
        new_pages = scrape_docs(new_url, max_pages=8)
        new_collection = store_in_chromadb(new_pages, collection_name="new_api")
        new_chunks = query_collection(new_collection, "API endpoints authentication base URL parameters", n_results=8)
        new_info = extract_api_info(new_chunks)

        changes = detect_changes(old_info, new_info)
        return jsonify(changes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500