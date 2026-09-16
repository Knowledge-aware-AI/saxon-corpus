import csv
import datetime
import json
import os
import sys
from pathlib import Path


CSV_HEADERS = ["ID", "Saxon", "German", "Webpage", "Date", "Source", "Origin", "Year", "Tags", "length"]


def normalize_paragraph(text):
    return " ".join(text.split())


def strip_wrapping_quotes(text):
    """Remove one pair of matching outer quotes from a string."""
    if not isinstance(text, str):
        return text

    text = text.strip()
    if len(text) >= 2 and ((text[0] == '"' and text[-1] == '"') or (text[0] == "'" and text[-1] == "'")):
        return text[1:-1]
    return text


def read_multiline_text(prompt_lines):
    print("\n".join(prompt_lines))
    print("Type END on its own line when you are done:\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break

        if line.strip() == "END":
            break

        lines.append(line)

    return normalize_paragraph("\n".join(lines))


def get_next_id(filepath):
    if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
        return 0

    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        max_id = -1

        for row in reader:
            raw_id = (row.get("ID") or "").strip()
            if not raw_id:
                continue

            try:
                max_id = max(max_id, int(raw_id))
            except ValueError:
                continue

    return max_id + 1 if max_id >= 0 else 0


def append_entry(filepath, saxon_text, german_text, webpage, date, source, origin, year, tags):
    entry_id = get_next_id(filepath)
    length = len(saxon_text)

    file_exists = os.path.exists(filepath)
    is_empty = file_exists and os.path.getsize(filepath) == 0

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists or is_empty:
            writer.writerow(CSV_HEADERS)

        writer.writerow([
            entry_id,
            saxon_text,
            german_text,
            webpage,
            date,
            source,
            origin,
            year,
            tags,
            length,
        ])


def append_json_entry(filepath, json_path):
    """Read one JSON file and append its content to the CSV.

    The JSON may be a single object or a list of objects. Missing fields are
    written as empty strings so the CSV keeps the expected column order.
    """
    file_exists = os.path.exists(filepath)
    is_empty = file_exists and os.path.getsize(filepath) == 0

    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    if isinstance(json_data, dict):
        entries = [json_data]
    elif isinstance(json_data, list):
        entries = json_data
    else:
        raise ValueError(f"Unsupported JSON structure in {json_path!r}")

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists or is_empty:
            writer.writerow(CSV_HEADERS)

        next_id = get_next_id(filepath)
        for entry in entries:
            if not isinstance(entry, dict):
                continue

            saxon_text = strip_wrapping_quotes(str(entry.get("Saxon", "")))
            writer.writerow([
                next_id,
                saxon_text,
                strip_wrapping_quotes(str(entry.get("German", ""))),
                str(entry.get("Webpage", "")),
                str(entry.get("Date", "")),
                strip_wrapping_quotes(str(entry.get("Source", ""))),
                strip_wrapping_quotes(str(entry.get("Origin", ""))),
                str(entry.get("Year", "")),
                strip_wrapping_quotes(str(entry.get("Tags", ""))),
                len(saxon_text),
            ])
            next_id += 1


def main():
    csv_path = os.path.join(os.path.dirname(__file__), "../..", "data.csv")
    csv_path = os.path.normpath(csv_path)

    saxon_text = read_multiline_text([
        "Paste the Saxon paragraph below.",
    ])

    if not saxon_text:
        print("No Saxon text entered.")
        sys.exit(0)

    add_german = input("Add German translation? [y/n] (Enter = n): ").strip().lower() or "n"
    while add_german not in ("y", "n"):
        add_german = input("Please enter y or n (Enter = n): ").strip().lower() or "n"

    german_text = ""
    if add_german == "y":
        german_text = read_multiline_text([
            "Paste the German translation below.",
        ])

    print("\n--- Entry preview ---")
    print(f"ID      : {get_next_id(csv_path)}")
    print(f"Saxon   : {saxon_text}")
    print(f"German  : {german_text}")

    print("\nEnter metadata for this entry:")
    webpage = input("Webpage: ").strip()

    today = datetime.date.today().isoformat()
    date_input = input(f"Date [{today}]: ").strip()
    date = date_input if date_input else today

    source = input("Source: ").strip()
    origin = input("Origin: ").strip()
    year = input("Year: ").strip()
    tags = input("Tags: ").strip()

    print("\n--- Batch summary ---")
    print(f"Webpage : {webpage}")
    print(f"Date    : {date}")
    print(f"Source  : {source}")
    print(f"Origin  : {origin}")
    print(f"Year    : {year}")
    print(f"Tags    : {tags}")
    print(f"Length  : {len(saxon_text)}")
    print("---------------------")

    confirm = input("\nWrite to CSV? [y/n] (enter = y): ").strip().lower()
    if confirm == "n":
        print("Aborted.")
        sys.exit(0)

    append_entry(csv_path, saxon_text, german_text, webpage, date, source, origin, year, tags)
    print(f"\n✓ Appended 1 row to: {csv_path}")


if __name__ == "__main__":
    main()
    #  for json_file in Path("webpages/lieder_anton_guenther/json").glob("*.json"):
    #      append_json_entry("data.csv", json_file)
    #      print(f"Appended entries from {json_file} to data.csv")