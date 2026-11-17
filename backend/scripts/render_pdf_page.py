
from pathlib import Path
import pymupdf

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "data" / "raw" / "tcs_annual_report_2025.pdf"
OUTPUT_PATH = BASE_DIR / "data" / "processed" / "page_307_original.png"


def render_page():
    doc = pymupdf.open(PDF_PATH)

    try:
        page = doc[306]  # PDF page 307, zero-based index

        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            alpha=False,
        )

        pix.save(OUTPUT_PATH)

        print("Rendered PDF page: 307")
        print("Output:", OUTPUT_PATH)

    finally:
        doc.close()


if __name__ == "__main__":
    render_page()
