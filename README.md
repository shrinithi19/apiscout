# 🔍 APIScout — Smart DevTool for API Integration

APIScout is an AI-powered developer tool that eliminates the need to manually read API documentation. Paste any REST API documentation URL and APIScout scrapes it, extracts every endpoint and authentication method, and instantly generates a production-ready Python wrapper class with full error handling.

---

## 🚀 Features

- **Automatic Endpoint Extraction** — Scrapes and analyzes API documentation to identify all available endpoints, methods, and parameters
- **Auth Detection** — Automatically identifies authentication methods (API Key, OAuth2, Bearer Token)
- **Python Wrapper Generation** — Generates a clean, typed, documented Python class ready to use in your project
- **Error Handling Intelligence** — Every generated method includes specific handlers for 400, 401, 404, 429, and 500 status codes
- **Natural Language to API Call** — Describe what you want in plain English and get the exact Python code instantly
- **API Changelog Detector** — Compare two versions of the same API documentation to detect added, removed, and modified endpoints
- **Round Robin Key Manager** — Cycles through multiple Gemini API keys to avoid rate limits

---

## 🎬 Demo Video

[![APIScout Demo](https://img.shields.io/badge/Watch%20Demo-YouTube-red?style=for-the-badge&logo=youtube)](YOUR_YOUTUBE_LINK_HERE)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask (Python) |
| AI Model | Gemini 2.5 Flash |
| Vector Store | ChromaDB |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Web Scraping | BeautifulSoup4 + Requests |
| Frontend | HTML, CSS, JavaScript |

---

## 📁 Project Structure

apiscout/

├── app/                  # Flask application

│   ├── templates/

│   │   └── index.html    # Frontend UI

│   ├── init.py       # App factory

│   └── routes.py         # API routes

├── scraper/              # Web scraping module

├── embedder/             # ChromaDB embedding pipeline

├── extractor/            # Gemini endpoint extraction

├── generator/            # Wrapper + NL code generation

├── changelog/            # API changelog detector

├── utils/

│   └── key_manager.py    # Round robin API key manager

├── main.py               # Entry point

├── requirements.txt      # Dependencies

└── .env                  # API keys (not committed)

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- Gemini API key (free from [Google AI Studio](https://aistudio.google.com))

### 1. Clone the repository
```bash
git clone https://github.com/shrinithi19/apiscout.git
cd apiscout
```

### 2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys
Create a `.env` file in the root directory:

GEMINI_API_KEY_1=your_gemini_api_key_here

GEMINI_API_KEY_2=your_second_key_here  # optional but recommended

### 5. Run the application
```bash
python main.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## 🎯 How to Use

1. **Paste a URL** — Enter any REST API documentation URL in the input field
2. **Click Scout it** — APIScout scrapes the docs and runs AI extraction (~30 seconds)
3. **Review Endpoints** — All found routes, methods, and parameters are listed
4. **Check Wrapper Code** — Copy or download the generated Python class
5. **Ask in English** — Describe what you want and get exact Python code instantly
6. **Changelog** — Compare two API versions to detect what changed

---

## 📌 Example

**Input URL:** `https://openweathermap.org/api`

**Generated wrapper (sample):**
```python
class OpenWeatherAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org"

    def get_current_weather(self, lat: float, lon: float) -> dict:
        """Returns current weather conditions for a location."""
        response = requests.get(
            f"{self.base_url}/data/4.0/onecall/current",
            params={"lat": lat, "lon": lon, "appid": self.api_key},
            timeout=10
        )
        if response.status_code == 401:
            raise PermissionError("Invalid API key")
        if response.status_code == 429:
            raise ConnectionAbortedError("Rate limit exceeded")
        return response.json()
```

---

## 🧠 Solution Approach

1. **Scraping** — BeautifulSoup recursively crawls the documentation URL and linked pages (up to 8 pages), removing noise like navigation, footers, and scripts

2. **Embedding** — Scraped text is chunked into 500-word overlapping segments and stored in ChromaDB using sentence-transformer embeddings

3. **Extraction** — The most relevant chunks are retrieved via semantic search and sent to Gemini 2.5 Flash with a structured prompt to extract endpoints, auth, and rate limits as JSON

4. **Generation** — Gemini generates a production-ready Python wrapper class based on the extracted API information, with full error handling and type hints

5. **NL to Code** — User queries in plain English are sent to Gemini along with the extracted endpoint list to generate specific API call code

6. **Changelog** — Two URLs are independently scraped and extracted, then compared structurally to detect added, removed, and modified endpoints

---

## 📋 Dependencies

flask

requests

beautifulsoup4

chromadb

google-generativeai

python-dotenv

sentence-transformers

lxml

gunicorn

---

## ⚠️ Limitations

- Works best with REST APIs that have HTML documentation pages
- JavaScript-rendered documentation may have limited extraction
- Generation takes ~30 seconds due to scraping + AI processing
- Free Gemini API tier has rate limits (mitigated with round-robin key manager)

---

## Colab Notebook

**Colab Notebook:** https://colab.research.google.com/drive/1m1Oxg5vkNQv0uf8tzFjbZTDfqDtsCSJV?usp=sharing

---

## 👩‍💻 Author

Built for the Claysys Tech AI Hackathon 2026.