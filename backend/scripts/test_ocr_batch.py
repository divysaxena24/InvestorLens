
from pathlib import Path
import pymupdf4llm

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf"
OUTPUT_DIR = BASE_DIR / "data" / "processed" / "ocr_tests"

# Zero-based indices: PDF pages 303, 304, 305, 307 and 313
PAGE_INDICES = [302, 303, 304, 306, 312]


def test_ocr_batch():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pages = pymupdf4llm.to_markdown(
        str(PDF_PATH),
        pages=PAGE_INDICES,
        page_chunks=True,
        force_ocr=True,
    )

    for page in pages:
        page_number = page["metadata"]["page_number"]
        output_path = OUTPUT_DIR / f"page_{page_number}.md"

        output_path.write_text(page["text"], encoding="utf-8")

        print(
            f"Saved PDF page {page_number} | "
            f"{len(page['text']):,} characters"
        )

    print("\nBatch OCR test completed.")


if __name__ == "__main__":
    test_ocr_batch()
