# InvestorLens Backend

The FastAPI-powered backend ingestion and financial intelligence pipeline for InvestorLens.

---

## Ingestion Architecture

```text
Raw PDF (e.g. TCS FY25)
       │
       ▼
[ PDFExtractionPipeline ] ──► Quality Checks & Header/Footer Inspection
       │                       ├── Printed page vs PDF page offset resolution
       │                       └── Quality Flags (replacements, mojibake, spacing, tables)
       ▼
[ SemanticChunker ] ────────► Structure-Aware Chunking (max_chars=3200, overlap_chars=400)
       │                       ├── Table header repetition across multi-row splits
       │                       ├── Safe unpacking of complex layout tables
       │                       └── Zero page-boundary crossing
       ▼
[ EmbeddingGenerator ] ─────► all-MiniLM-L6-v2 (384-dimensional dense vectors)
       │
       ▼
[ Persistence & Validation ] ─► Compressed NumPy (.npz) + JSON Metadata
```

---

## Directory Layout

```text
backend/
├── app/
│   ├── ingestion/
│   │   ├── models.py          # PageExtraction, DocumentChunk, PageComparison
│   │   ├── quality.py         # Quality heuristic checker & anomaly detection
│   │   ├── metadata.py        # Spatial header/footer metadata extractor
│   │   ├── extractor.py       # Native extraction & selective OCR coordinator
│   │   ├── compare.py         # Non-destructive native-vs-OCR diff checker
│   │   ├── report.py          # Extraction quality CSV generator
│   │   ├── chunker.py         # Structure-aware semantic chunker
│   │   └── embeddings.py      # Dense vector embedding generator
│   ├── main.py                # FastAPI app initialization and health endpoints
│   └── ...                    # Core, models, retrieval, financial services
├── data/
│   ├── raw/                   # Source documents
│   └── processed/             # Extraction outputs, quality reports, and embeddings
├── scripts/
│   ├── extract_pdf.py         # Extracts PDF to Markdown with full quality report
│   ├── compare_extraction.py  # Selective OCR comparison and ratio verification
│   ├── render_pdf_page.py     # High-resolution PDF page image renderer
│   ├── test_embeddings.py     # Standalone semantic similarity test script
│   └── embed_document.py      # Complete end-to-end ingestion & embedding pipeline
├── tests/                     # Pytest suite with 35+ test cases
└── pyproject.toml             # Python 3.12 dependencies and configuration
```

---

## Setup & Running

### 1. Environment Setup

```bash
uv sync
```

### 2. Run Test Suite

```bash
uv run pytest
```

### 3. Pipeline CLI Commands

- **Run Full Native Extraction & Quality Audit**:
  ```bash
  uv run python scripts/extract_pdf.py --pdf data/raw/tcs_annual_report_2025.pdf
  ```

- **Run Selective OCR & Verification on Page 307**:
  ```bash
  uv run python scripts/compare_extraction.py --pages 307
  ```

- **Run Complete End-to-End Ingestion & Embedding Pipeline**:
  ```bash
  uv run python scripts/embed_document.py --pdf data/raw/tcs_annual_report_2025.pdf
  ```
