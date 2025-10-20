# Minimal job scraper template for job_scraper repo
# Replace the example URL and parsing logic with the real target site and selectors.

import requests
from bs4 import BeautifulSoup

def fetch(url: str) -> str:
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

def parse(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # Example: find job titles — update selector to match the site you scrape
    titles = [t.get_text(strip=True) for t in soup.select(".job-title")]
    return titles

def main():
    url = "https://example.com/jobs"
    html = fetch(url)
    jobs = parse(html)
    for i, title in enumerate(jobs, 1):
        print(f"{i}. {title}")

if __name__ == "__main__":
    main()
