from pathlib import Path
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

# -----------------------------
# Configuration
# -----------------------------
INDEX_URL = "https://www.sachsen-lese.de/streifzuege/lieder/lieder-von-anton-guenther/?page=3"

OUTPUT_DIR = Path("webpages/lieder_anton_guenther/html/")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()
session.headers.update(HEADERS)

# -----------------------------
# Download the index page
# -----------------------------
print("Downloading index page...")
response = session.get(INDEX_URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# -----------------------------
# Collect unique poem links
# -----------------------------
links = {}

for a in soup.select('a.linkTitle[href*="/streifzuege/lieder/lieder-von-anton-guenther/"]'):
    title = a.get_text(strip=True)
    url = urljoin(INDEX_URL, a["href"])

    # Remove duplicates (there are a few on the page)
    links[url] = title

print(f"Found {len(links)} unique poem pages.")

# -----------------------------
# Download each poem page
# -----------------------------
for url, title in links.items():
    slug = url.rstrip("/").split("/")[-1]
    outfile = OUTPUT_DIR / f"{slug}.html"

    if outfile.exists():
        print(f"Skipping {title}")
        continue

    try:
        r = session.get(url, timeout=20)
        r.raise_for_status()

        outfile.write_text(r.text, encoding="utf-8")
        print(f"Downloaded: {title}")

    except Exception as e:
        print(f"Failed: {title}")
        print(e)

print("Done.")