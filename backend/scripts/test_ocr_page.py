
from pathlib import Path
import pymupdf4llm

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "ocr_page_300.md"

# PDF page 300; page indices are zero-based.
pages = pymupdf4llm.to_markdown(
    str(PDF_PATH),
    pages=[299],
    page_chunks=True,
    force_ocr=True
)

page = pages[0]

OUTPUT_PATH.write_text(
    page["text"],
    encoding="utf-8"
)

print("OCR test completed")
print("Page:", page["metadata"]["page_number"])
print("Characters:", len(page["text"]))
print("Output:", OUTPUT_PATH)
print("\nExtracted content:\n")
print(page["text"][:5000])
