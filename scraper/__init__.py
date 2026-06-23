import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def scrape_docs(start_url: str, max_pages: int = 10) -> dict[str, str]:
    """
    Scrapes documentation from a given URL recursively.
    Returns a dict of {url: page_text_content}
    """
    visited = set()
    pages_content = {}
    base_domain = urlparse(start_url).netloc

    def scrape_page(url: str):
        if url in visited or len(visited) >= max_pages:
            return
        
        visited.add(url)
        print(f"Scraping: {url}")

        try:
            response = requests.get(url, timeout=10, headers={
                "User-Agent": "Mozilla/5.0"
            })
            if response.status_code != 200:
                print(f"Skipping {url} — status {response.status_code}")
                return

            soup = BeautifulSoup(response.text, "lxml")

            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Skip pages with very little content
            if len(text) < 200:
                print(f"Skipping {url} — too little content")
                return
            pages_content[url] = text

            # Find all links on this page
            for a_tag in soup.find_all("a", href=True):
                link = urljoin(url, a_tag["href"])
                parsed = urlparse(link)

                # Only follow links on the same domain
                clean_link = link.split("#")[0]
                if parsed.netloc == base_domain and clean_link not in visited and clean_link:
                    scrape_page(clean_link)

        except Exception as e:
            print(f"Error scraping {url}: {e}")

    scrape_page(start_url)
    return pages_content


if __name__ == "__main__":
    results = scrape_docs("https://openweathermap.org/api", max_pages=5)
    for url, content in results.items():
        print(f"\n--- {url} ---")
        print(content[:300])