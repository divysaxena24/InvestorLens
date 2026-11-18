# InvestorLens 2.0

> Enterprise-grade AI-powered financial intelligence & annual report analysis engine.

InvestorLens 2.0 transforms long, complex corporate financial documents (e.g., 300+ page integrated annual reports) into structured, verifiable financial intelligence using deterministic financial validations, hybrid document retrieval, structure-aware semantic chunking, and Retrieval-Augmented Generation (RAG).

---

## Key Features

- **Validated PDF Ingestion**: High-fidelity native PDF extraction via `pymupdf4llm` combined with selective OCR using `rapidocr_onnxruntime` for corrupted glyphs and font CMaps.
- **Extraction Quality Assurance**: Automated per-page anomaly detection flagging Unicode replacement characters (``), mojibake encoding issues, suspicious Greek-substituted digits, broken kerning/word spacing, and malformed tables.
- **Accurate Metadata Preservation**: Header/footer spatial bounding-box inspection mapping PDF pages to true printed report page numbers (resolving multi-page offsets) and document sections without hallucination.
- **Structure-Aware Semantic Chunking**: Strictly enforced chunk limits (`max_chars=3200`, `overlap_chars=400`) that repeat table headers/separators across splits, unpack complex layout-derived tables, prevent split-sentence mid-word truncation, and maintain full page provenance across every chunk.
- **Dense Vector Embedding Pipeline**: Normalised 384-dimensional dense vectors generated via `sentence-transformers/all-MiniLM-L6-v2` with unit L2 norm verification and compressed NumPy (`.npz`) persistence.
- **Deterministic Discrepancy Checks**: Non-destructive comparison preserving native financial data while highlighting OCR variations for human auditor verification.
- **Tested & Verified Pipeline**: Over 35 unit and integration tests with 100% pass rate covering extraction, metadata offset resolution, quality checks, chunk size boundaries, table headers, and embedding vector constraints.

---

## Architecture & Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.12, FastAPI, Uvicorn | Async high-performance REST API |
| **PDF Extraction & OCR** | PyMuPDF, pymupdf4llm, RapidOCR ONNX | Native markdown extraction & targeted fallback OCR |
| **Chunking & NLP** | Custom SemanticChunker, Sentence-Transformers | Structure-aware chunking & `all-MiniLM-L6-v2` embeddings |
| **Vector Storage (Upcoming)** | Qdrant | Dense vector search and payload filtering |
| **Relational Storage (Upcoming)** | PostgreSQL, SQLAlchemy / Alembic | Document metadata, user research sessions, and audit logs |
| **LLM Reasoning (Upcoming)** | Groq / Llama 3 | Fast financial RAG inference and qualitative analysis |
| **Frontend (Upcoming)** | Next.js 15, TypeScript, Tailwind CSS | Modern financial analyst workspace UI |

---

## Project Structure

```text
InvestorLens/
├── backend/
│   ├── app/
│   │   ├── ingestion/             # PDF extraction, quality checks, chunking & embeddings
│   │   │   ├── chunker.py         # Structure-aware semantic chunker
│   │   │   ├── compare.py         # Native vs OCR diff & discrepancy checker
│   │   │   ├── embeddings.py      # Dense vector embedding generator
│   │   │   ├── extractor.py       # End-to-end PDF extraction pipeline
│   │   │   ├── metadata.py        # Header/footer metadata & page offset extractor
│   │   │   ├── models.py          # Data models (PageExtraction, DocumentChunk, etc.)
│   │   │   ├── quality.py         # Extraction quality heuristics & anomaly flags
│   │   │   └── report.py          # Quality audit CSV report generator
│   │   ├── main.py                # FastAPI entry point & health endpoints
│   │   └── ...                    # Retrieval, financial & analyst modules
│   ├── data/
│   │   ├── raw/                   # Raw annual reports (e.g. TCS Annual Report 2024-25)
│   │   └── processed/             # Extracted Markdown, CSV audits & compressed embeddings
│   ├── scripts/
│   │   ├── extract_pdf.py         # Native PDF extraction script
│   │   ├── compare_extraction.py  # Selective OCR comparison script
│   │   ├── embed_document.py      # End-to-end extraction -> chunking -> embedding pipeline
│   │   └── render_pdf_page.py     # High-res PDF page renderer
│   ├── tests/                     # Comprehensive pytest test suite (35+ unit & integration tests)
│   └── pyproject.toml             # Backend dependencies managed with uv
├── docs/                          # Architecture & business requirements documentation
└── frontend/                      # Next.js web application
```

---

## Current Status & Real-World Validation

### TCS Integrated Annual Report 2024-25 (336 Pages)
- **Extraction**: Processed 336 pages to Markdown (~1.16M characters) with a complete quality audit CSV.
- **Selective OCR Validation**: PDF Page 307 (Printed Page 305, Standalone Financial Statements Note 25) validated against rendered high-res image; all 10 financial ratios verified with OCR recovering glyph-corrupted values without overwriting native output.
- **Chunking**: Generated **532 chunks** strictly bounded by `max_chars=3200` (min: 9, max: 3,200). Complex layout tables (e.g., Pages 66-67 AGM notices) safely unpacked with zero size violations.
- **Dense Embeddings**: Generated **532 normalized 384-dimensional vectors** (100% finite, unit L2 norm, unique chunk IDs) stored compactly in `tcs_annual_report_2025_vectors.npz` (732 KB) and `tcs_annual_report_2025_chunks.json`.

---

## Getting Started

### Prerequisites
- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) (recommended) or `pip`

### Setup Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run test suite:
   ```bash
   uv run pytest
   ```

4. Run the end-to-end ingestion & embedding pipeline:
   ```bash
   uv run python scripts/embed_document.py --pdf data/raw/tcs_annual_report_2025.pdf
   ```
