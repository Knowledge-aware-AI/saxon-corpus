import os
import json
import datetime
from openai import OpenAI
from pathlib import Path
from urllib.parse import urljoin

# Load API key from environment variable
my_api_key = os.getenv("API_KEY")

# Check if API key exists
if my_api_key:
    print("API key loaded successfully")
else:
    print("No API key found")

# Initialize the client
client = OpenAI(base_url="https://llm.scads.ai/v1", api_key=my_api_key)
model_name = "zai-org/GLM-5.2-FP8"


# Get prompt and HTML files
prompt = Path("src/llm/prompts/extract_from_html.md").read_text(encoding="utf-8")
html_files = list(Path("webpages/lieder_anton_guenther/html").glob("*.html"))
base_url = "https://www.sachsen-lese.de/streifzuege/lieder/lieder-von-anton-guenther/"


def extract_text_from_html(prompt, html_files, base_url):
    count = 0

    for page in html_files:
        html_content = page.read_text(encoding="utf-8")

        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt + html_content}],
                model=model_name,
            )
            
            result = response.choices[0].message.content
            page_url = urljoin(base_url, f"{page.stem}/")
            today = datetime.date.today().isoformat()
            result = f"{result}\n\nDate: {today}\nWebpage: {page_url}\nTags: poetry\n"
            output_path = Path("webpages/lieder_anton_guenther/txt/") / f"{page.stem}.txt"
            output_path.write_text(result, encoding="utf-8")
            print(f"Extraction successful for {page.name}")
            count += 1
            
        
        except Exception as e:
            print(f"Error during extraction for {page.name}: {e}")
            
    print(f"\nExtraction completed for {count} out of {len(html_files)} pages.")

def txt_to_json(file):
    content = file.read_text(encoding="utf-8")
    keys = ["Saxon", "Source", "Origin", "Year", "Date", "Webpage", "Tags"]
    data = {key: "" for key in keys}
    current_key = None

    for raw_line in content.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("Here is the extracted information"):
            continue

        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()

            if key in data:
                data[key] = value.strip()
                current_key = key
                continue

        if current_key is not None:
            if data[current_key]:
                data[current_key] += "\n" + line
            else:
                data[current_key] = line

    return data

if __name__ == "__main__":
#     extract_text_from_html(prompt, html_files, base_url)
     for txt_file in Path("webpages/lieder_anton_guenther/txt").glob("*.txt"):
         json_data = txt_to_json(txt_file)
         json_file = Path("webpages/lieder_anton_guenther/json") / f"{txt_file.stem}.json"
         json_file.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
