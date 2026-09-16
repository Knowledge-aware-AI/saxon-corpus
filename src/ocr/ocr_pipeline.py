#!/usr/bin/env python3
"""
frktur OCR Pipeline (Linux / WSL)
==================================
Renders a scanned frktur PDF → preprocesses each page → runs Tesseract
(frk and/or deu model) → post-processes the text.

Usage
-----
  python ocr_pipeline.py book.pdf
  python ocr_pipeline.py book.pdf --dpi 600 --start 5 --end 10
  python ocr_pipeline.py book.pdf --save-images          # debug
  python ocr_pipeline.py book.pdf --lang deu             # try regular German
  python ocr_pipeline.py book.pdf --both                 # run frk + deu, save both
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
from pypdf import PdfReader   # add to imports at top
from kraken import pageseg, binarization, rpred, blla
from kraken.lib import models

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR = _REPO_ROOT / "models"
_KRAKEN_MODEL = None
_KRAKEN_MODEL_PATH: Path | None = None

# ======================================================================
#  STEP 1  —  PDF → page images (one at a time to avoid OOM)
# ======================================================================


def get_page_count(pdf_path: str) -> int:
    """Cheaply count pages without rendering them."""
    return len(PdfReader(pdf_path).pages)


def render_single_page(pdf_path: str, page_num: int, dpi: int = 400) -> Image.Image:
    """Render one page (1-indexed) — peak memory = 1 page."""
    images = convert_from_path(
        pdf_path, dpi=dpi, first_page=page_num, last_page=page_num,
    )
    return images[0]
# ======================================================================
#  STEP 2  —  image pre-processing
# ======================================================================

def _deskew(gray: np.ndarray) -> np.ndarray:
    """Straighten a slightly rotated page."""
    coords = np.column_stack(np.where(gray < 128))
    if len(coords) < 100:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255,
    )


def preprocess(pil_img: Image.Image, engine: str) -> np.ndarray:
    img = np.array(pil_img.convert("L"))
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Gentle denoise — just enough to smooth scan artifacts
    img = cv2.fastNlMeansDenoising(img, h=7)

    if engine == "tesseract":
        # Mild contrast enhancement — no forced black/white
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

    img = _deskew(img)
    return img


# # ======================================================================
# #  STEP 3  —  OCR
# # ======================================================================

# TESSERACT

_TESSERACT_CONFIG = "--oem 1 --psm 4"


def ocr_with_tesseract(img: np.ndarray, lang: str) -> str:
    """Run Tesseract OCR on a preprocessed image."""
    return pytesseract.image_to_string(img, lang=lang, config=_TESSERACT_CONFIG)


# KRAKEN

def _resolve_kraken_model(model_name: str) -> Path:
    candidate = Path(model_name)
    if candidate.is_file():
        return candidate

    if candidate.suffix != ".mlmodel":
        candidate = candidate.with_suffix(".mlmodel")

    resolved = _MODELS_DIR / candidate.name
    if resolved.is_file():
        return resolved

    available = ", ".join(sorted(p.stem for p in _MODELS_DIR.glob("*.mlmodel"))) or "<none>"
    raise FileNotFoundError(
        f"Unknown Kraken model '{model_name}'. Available models: {available}"
    )


def ocr_with_kraken(img: np.ndarray, model_name: str) -> str:
    global _KRAKEN_MODEL
    global _KRAKEN_MODEL_PATH

    model_path = _resolve_kraken_model(model_name)
    if _KRAKEN_MODEL is None or _KRAKEN_MODEL_PATH != model_path:
        print("[Kraken] Loading model…")
        _KRAKEN_MODEL = models.load_any(str(model_path))
        _KRAKEN_MODEL_PATH = model_path
        print(f"[Kraken] Model loaded: {model_path}")

    pil_img = Image.fromarray(img)
    print(f"[Kraken] Input image: {pil_img.size} mode={pil_img.mode}")

    pil_img = binarization.nlbin(pil_img)
    print(f"[Kraken] Binarization done: mode={pil_img.mode}")

    segments = blla.segment(pil_img)
    # Kraken 5.x returns a SegmentationResult; lines are in .lines
    seg_lines = segments.lines if hasattr(segments, 'lines') else segments
    print(f"[Kraken] Segmentation done: {len(seg_lines)} lines found")

    result = rpred.rpred(_KRAKEN_MODEL, pil_img, segments)
    lines = []
    for r in result:
        text = getattr(r, "prediction", None) or getattr(r, "text", None)
        if text:
            lines.append(text)
    print(f"[Kraken] OCR done: {len(lines)} text lines extracted")

    return "\n".join(lines)


def ocr_page(img: np.ndarray, engine: str, model_name: str) -> str:
    if engine == "kraken":
        return ocr_with_kraken(img, model_name)
    if engine == "tesseract":
        return ocr_with_tesseract(img, model_name)
    raise ValueError(f"Unsupported OCR engine: {engine}")

# ======================================================================
#  STEP 4  —  post-processing
# ======================================================================

# Common frktur OCR misreads — extend this dict as you review output.
# The keys are what OCR gets *wrong*; the values are the fix.
frkTUR_FIXES: dict[str, str] = {
    # --- 'f' read instead of long-s 'ſ' ---
    "fid":    "sind",
    "find":   "sind",
    "fich":   "sich",
    "foll":   "soll",
    "fein":   "sein",
    "feyn":   "seyn",
    "fchon":  "schon",
    "fchwer": "schwer",
    "fcb":    "sch",
    # --- 'v' read instead of 'u' (frktur u has an Überstrich) ---
    "vnd":  "und",
    "vber": "über",
    "vm":   "um",
    "vns":  "uns",
    # --- 'n' read instead of 'u' ---
    "nnd": "und",
    # --- other frequent confusions ---
    "audh": "auch",
    "iod":  "und",
}


def postprocess(raw: str) -> str:
    """Clean up OCR output: long-s, common errors, whitespace."""

    text = raw

    # 1. Normalise long-s  ſ → s
    text = text.replace("ſ", "s")

    # 2. Word-level fixes from the dictionary above
    words = text.split()
    fixed = []
    for w in words:
        bare = re.sub(r'[^\wäöüßÄÖÜ]', '', w, flags=re.UNICODE)
        if bare in frkTUR_FIXES:
            w = w.replace(bare, frkTUR_FIXES[bare])
        fixed.append(w)
    text = ' '.join(fixed)

    # 3. Whitespace cleanup
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = '\n'.join(line.strip() for line in text.split('\n'))

    return text.strip()


# ======================================================================
#  MAIN
# ======================================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="OCR a frktur PDF → clean text (Kraken or Tesseract)."
    )
    parser.add_argument("--pdf", default="src/ocr/pdfs/de_saeksche_schweiz.pdf", help="Path to the input PDF.")
    parser.add_argument(
        "--engine",
        choices=["kraken", "tesseract"],
        default="tesseract",
        help="OCR backend to use (default: tesseract).",
    )
    parser.add_argument(
        "--output-dir", default="src/ocr/output",
        help="Base directory for OCR outputs (a backend/model subfolder will be created inside it).",
    )
    parser.add_argument(
        "--dpi", type=int, default=400,
        help="Render DPI (default: 400).",
    )
    parser.add_argument(
        "--start", type=int, default=0,
        help="First page, 0-indexed (default: 0).",
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="Last page, exclusive (default: all).",
    )
    parser.add_argument(
        "--kraken-model",
        choices=sorted(p.stem for p in _MODELS_DIR.glob("*.mlmodel")),
        default="german_print",
        help="Kraken model to use (default: german_print).",
    )
    parser.add_argument(
        "--tesseract-lang",
        choices=["frk", "deu"],
        default="frk",
        help='Tesseract language code to use (default: "frk").',
    )
    parser.add_argument(
        "--save-images", action="store_true",
        help="Save preprocessed page images (for debugging).",
    )
    args = parser.parse_args()
    
    # Debugging args
    args.start = 8
    args.end = 9
    args.save_images = True
    args.engine = "kraken"
    args.kraken_model = "austriannewspapers"


    model_label = args.kraken_model if args.engine == "kraken" else args.tesseract_lang
    out = Path(args.output_dir) / f"{args.engine}_{model_label}"
    txt_out = out / "txt"
    png_out = out / "png"
    out.mkdir(parents=True, exist_ok=True)
    txt_out.mkdir(parents=True, exist_ok=True)
    png_out.mkdir(parents=True, exist_ok=True)

    # === STEP 1: get page count ===
    total_pages = get_page_count(args.pdf)
    start = args.start
    end = args.end if args.end is not None else total_pages
    print(f"[1] {total_pages} pages total, processing {start+1}–{end}")
    print(f"    Engine/model → {args.engine} / {model_label}")
    print(f"    Output dir   → {out}")

    all_pages: list[str] = []

    for page_num in range(start + 1, end + 1):      # 1-indexed
        page_no = page_num

        # Render ONE page, then let it be garbage-collected
        pil_img = render_single_page(args.pdf, page_num, dpi=args.dpi)
        print(f"\n{'='*50}")
        print(f"  Page {page_no}")
        print(f"{'='*50}")

        # === STEP 2: preprocess ===
        print("[2] Preprocessing …")
        img = preprocess(pil_img, args.engine)

        if args.save_images:
            dbg = png_out / f"debug_page_{page_no:04d}.png"
            cv2.imwrite(str(dbg), img)
            print(f"    Debug image → {dbg}")

        # === STEP 3: OCR ===
        print(f"[3] OCR (engine={args.engine}) …")
        raw = ocr_page(img, args.engine, model_label)
        clean = postprocess(raw)


        all_pages.append(clean)

        pf = txt_out / f"page_{page_no:04d}.txt"
        pf.write_text(clean, encoding="utf-8")
        print(f"    → {pf}")

    # --- Save combined text ---
    combined = txt_out / "full_text.txt"
    combined.write_text(
        "\n\n--- PAGE BREAK ---\n\n".join(all_pages),
        encoding="utf-8",
    )

    print(f"\n{'='*50}")
    print(f"✅  Done!  {len(all_pages)} page(s) processed.")
    print(f"    Combined text  → {combined}")
    print(f"    Individual pages → {txt_out}/page_*.txt")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()