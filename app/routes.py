from flask import Blueprint, request, jsonify, render_template
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import scrape_docs
from embedder import store_in_chromadb, query_collection
from extractor import extract_api_info
from generator import generate_wrapper, generate_nl_to_api

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