import csv
import os
import re
import sys
import datetime

# ----------------------------------------------------------------------
# Sentence splitting (zero dependencies)
# ----------------------------------------------------------------------
_ABBREVS = {
"Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "St.", "vs.", "etc.",
"e.g.", "i.e.", "Vol.", "vol.", "pp.", "Inc.", "Ltd.", "Co.", "Corp.",
"LLC", "LLP", "U.S.", "U.K.", "U.N.", "E.U.", "A.M.", "P.M.",
"No.", "Nos.", "et al.", "ibid.", "id.", "op. cit.", 
"z.B.", "usw.", "ca.", "u.a.", "bzw.", "d.h.", "sog.", "sogt.", "vgl.", "vgls.", "s.ä.", "s.o.",
}

def split_sentences(text):
    if not text:
        return []
    
    # Remove extra whitespace and normalize
    text = " ".join(text.strip().split())
    
    # Handle abbreviations
    placeholders = {}
    for abbr in sorted(_ABBREVS, key=len, reverse=True):
        if abbr in text:
            ph = f"§§{len(placeholders)}§§"
            text = text.replace(abbr, ph)
            placeholders[ph] = abbr
    
    # Split by sentence endings first
    parts = re.split(r"(?<=[.!?])\s+", text)
    sentences = []
    
    for part in parts:
        # Restore abbreviations
        for ph, abbr in placeholders.items():
            part = part.replace(ph, abbr)
        part = part.strip()
        
        # Now split on | characters within each sentence part
        if '|' in part:
            sub_parts = part.split('|')
            # Remove empty parts and strip whitespace
            sub_parts = [sub_part.strip() for sub_part in sub_parts if sub_part.strip()]
            sentences.extend(sub_parts)
        elif part:
            sentences.append(part)
    
    return sentences

# ----------------------------------------------------------------------
# CSV writing
# ----------------------------------------------------------------------
def append_rows(filepath, sentences, language, webpage, date, source, origin, year, tags):
    file_exists = os.path.exists(filepath)
    is_empty = file_exists and os.path.getsize(filepath) == 0

    with open(filepath, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists or is_empty:
            writer.writerow(["Saxon", "German", "Webpage", "Date", "Source", "Origin", "Year", "Tags"])

        for sent in sentences:
            if language == "Saxon":
                row = [sent, "", webpage, date, source, origin, year, tags]
            else:
                row = ["", sent, webpage, date, source, origin, year, tags]
            writer.writerow(row)

# ----------------------------------------------------------------------
# Main flow
# ----------------------------------------------------------------------
def main():
    csv_path = "../data.csv"

    print("\nPaste your paragraph below.")
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

    paragraph = "\n".join(lines)
    sentences = split_sentences(paragraph)

    if not sentences:
        print("No sentences found.")
        sys.exit(0)

    print("\n--- Sentences detected ---")
    for i, sent in enumerate(sentences, 1):
        print(f"{i}. {sent}")
    print("--------------------------")

    while True:
        action = input("\nAccept sentences? [y/n/edit]: ").strip().lower()
        if action == "n":
            print("Aborted.")
            sys.exit(0)
        elif action == "edit":
            edited = []
            i = 0
            while i < len(sentences):
                sent = sentences[i]
                print(f"\n{i+1}. {sent}")
                choice = input("Keep [k], Remove [r], Edit [e], Split [s], Merge with next [m], Finish [f]? ").strip().lower()
                
                if choice == 'r':
                    i += 1
                    continue
                elif choice == 'e':
                    # Direct sentence editing - print current sentence and get new one
                    print(f"Current sentence: {sent}")
                    new = input("Enter new sentence: ").strip()
                    if new:
                        # Check if the new sentence contains a split marker "|"
                        if "|" in new:
                            # Split into two sentences at the marker
                            parts = new.split("|")
                            if len(parts) == 2:
                                edited.append(parts[0].strip())
                                edited.append(parts[1].strip())
                            else:
                                # If multiple | markers, treat as single sentence
                                edited.append(new)
                        else:
                            # Regular edit
                            edited.append(new)
                    else:
                        edited.append(sent)
                    i += 1
                elif choice == 's':
                    # Split into two sentences
                    print(f"Current sentence: {sent}")
                    first_part = input("Enter the first part of the split sentence: ").strip()
                    second_part = input("Enter the second part of the split sentence: ").strip()
                    if first_part and second_part:
                        edited.append(first_part)
                        edited.append(second_part)
                    elif first_part:
                        edited.append(first_part)
                    elif second_part:
                        edited.append(second_part)
                    else:
                        edited.append(sent)
                    i += 1
                elif choice == 'm':
                    # Merge with next sentence if exists
                    if i + 1 < len(sentences):
                        merged = sent + " " + sentences[i+1]
                        edited.append(merged)
                        i += 2  # Skip the next sentence since we merged it
                    else:
                        # If no next sentence, just keep current
                        edited.append(sent)
                        i += 1
                elif choice == 'f':
                    # Finish editing and continue with remaining sentences
                    # Add any remaining sentences that weren't processed yet
                    while i < len(sentences):
                        edited.append(sentences[i])
                        i += 1
                    sentences = edited
                    break
                else:
                    edited.append(sent)
                    i += 1
                    
            if action != 'f':  # If we didn't finish editing via 'f' command
                sentences = edited
                
            if not sentences:
                print("No sentences left. Aborted.")
                sys.exit(0)
            
            # Reprint sentences after editing
            print("\n--- Sentences after editing ---")
            for i, sent in enumerate(sentences, 1):
                print(f"{i}. {sent}")
            print("--------------------------")
        else:  # action == "y"
            break

    # --- Language choice (per paragraph) ---
    print("\nSelect language for this paragraph:")
    print("1. Saxon")
    print("2. German")
    lang_choice = input("Choice [1/2]: ").strip()
    while lang_choice not in ("1", "2"):
        lang_choice = input("Please enter 1 or 2: ").strip()
    language = "Saxon" if lang_choice == "1" else "German"

    # --- Metadata (per paragraph) ---
    print("\nEnter metadata for this batch:")
    webpage = input("Webpage: ").strip()

    today = datetime.date.today().isoformat()   # e.g. 2025-01-14
    date_input = input(f"Date [{today}]: ").strip()
    date = date_input if date_input else today

    source = input("Source: ").strip()
    origin = input("Origin: ").strip()
    year   = input("Year: ").strip()
    tags   = input("Tags: ").strip()

    # --- Preview ---
    print("\n--- Batch summary ---")
    print(f"Language : {language}")
    print(f"Sentences: {len(sentences)}")
    print(f"Webpage  : {webpage}")
    print(f"Date     : {date}")
    print(f"Source   : {source}")
    print(f"Origin   : {origin}")
    print(f"Year     : {year}")
    print(f"Tags     : {tags}")
    print("---------------------")

    confirm = input("\nWrite to CSV? [y/n]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    append_rows(csv_path, sentences, language, webpage, date, source, origin, year, tags)
    print(f"\n✓ Appended {len(sentences)} row(s) to: {csv_path}")

if __name__ == "__main__":
    main()