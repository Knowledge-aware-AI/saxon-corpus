# SaxonLLM

The associated report can be found [here](Report.pdf)

# Data Sources

## [Wikipedia](https://web.archive.org/web/20260102120948/http://incubator.wikimedia.org/wiki/Wp/sxu/Main_Page) and [SimplySaxony Instagram](https://www.instagram.com/simplysaxony/)

1. extracted [by line](/src/text_to_corpus/sentence_extraction.py) first
2. later edited to whole page per entry with [combine_consecutive_rows(df)](/src/corpus.py)

## [Sachsen-Lese](https://www.sachsen-lese.de/) Mundartliches & Lieder von Anton Günther
1. [.html files](./webpages/) scraped with [webpage_scraping.py](./src/webpage_scraping.py)
2. turned into [.txt files](./webpages/) with LLM call and static processing via [saxon_extraction.py](./src/llm/saxon_extraction.py)
3. turned into [.json files](./webpages/json/) via [saxon_extraction.py](./src/llm/saxon_extraction.py)
4. JSON files cleaned manually

## Other webpages
Found via google search, mostly just a few sentences or paragraphs  
See entries with empty "Tag" column in [data](data.csv)

# LLM extraction

- Parsed https://www.sachsen-lese.de/streifzuege/mundartliches/ with **meta-llama/Llama-3.3-70B-Instruct**:
    - often correct text extraction, sometimes missing parts or wrong order of paragraphs
    - mostly wrong year
    - sometimes wrong source/origin

    - NOTE: formatting differs heavily

- Parsed https://www.sachsen-lese.de/streifzuege/lieder/lieder-von-anton-guenther/ with **zai-org/GLM-5.2-FP8**:
    - perfect text extraction
    - perfect author
    - mostly correct year and origin

    - NOTE: mostly unified formatting


# OCR

Both engines with different models did not result in significant improvements to existing OCRs, see [output](src/ocr/output)

### [Tesseract](https://github.com/tesseract-ocr/tesseract)
Inaccurate recognition, with *deu* and *frk*

### [Kraken](https://github.com/mittagessen/kraken)
Less artefacts than Tesseract, but equally inaccurate recognition
No improvement with either model *german_print* and *austriannewspapers*