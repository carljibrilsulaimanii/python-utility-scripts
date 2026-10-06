# extract_all_text.py
# Author: Jibril Sulaiman
# What:   Pulls every word out of a PDF: the normal text layer of each page, plus OCR
#         (Tesseract) on a ~150 DPI render of the same page, so text that only exists
#         inside screenshots, scans or images is captured too. Writes one combined
#         ALL_TEXT.txt with a DIRECT + OCR section per page.
# Why:    Chat assistants' built-in file tools read the text layer only. Their OCR runs
#         kept timing out mid-document ("Code interpreter session expired") and came
#         back with empty OCR sections. Running it locally has no time limit.
# Run:    pip install pytesseract pillow pymupdf   (and install Tesseract itself)
#         python extract_all_text.py "document.pdf"

import sys, re, io, hashlib, json
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

def norm(s):
    s = s.replace("\r","\n")
    s = re.sub(r"\t"," ",s)
    s = re.sub(r" +"," ",s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

pdf_path = sys.argv[1]
doc = fitz.open(pdf_path)
pages = []
for i, page in enumerate(doc, start=1):
    direct = norm(page.get_text("text"))
    # ~150 dpi render
    mat = fitz.Matrix(2.1, 2.1)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    ocr = pytesseract.image_to_string(img)
    ocr = norm(ocr)
    combined = f"{direct}\n\n--- OCR TEXT (Page {i}) ---\n{ocr}"
    pages.append(f"=== PAGE {i} — DIRECT + OCR ===\n{combined}")

doc.close()

open("ALL_TEXT.txt","w",encoding="utf-8").write("\n\n".join(pages))
print("Wrote ALL_TEXT.txt")
