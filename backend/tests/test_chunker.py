from app.ingestion.chunker import SemanticChunker
from app.ingestion.models import PageExtraction


def make_page(
    text,
    page=10,
    printed=8,
    section="Standalone Financial Statements",
    review=False,
    flags=None,
    method="native",
):
    return PageExtraction(
        pdf_page=page,
        printed_page=printed,
        section=section,
        text=text,
        extraction_method=method,
        review_required=review,
        quality_flags=flags or [],
    )


def test_chunk_preserves_page_metadata():
    page = make_page("Revenue increased during FY2025.")

    chunks = SemanticChunker().chunk_pages([page], "tcs_2025")

    assert len(chunks) == 1
    assert chunks[0].document_id == "tcs_2025"
    assert chunks[0].page_start == 10
    assert chunks[0].printed_page == 8
    assert chunks[0].section == "Standalone Financial Statements"


def test_review_status_and_quality_flags_are_preserved():
    page = make_page(
        "Financial figures require verification.",
        review=True,
        flags=["UNICODE_REPLACEMENT_CHAR(3)"],
    )

    chunks = SemanticChunker().chunk_pages([page], "tcs_2025")

    assert chunks[0].review_required is True
    assert "UNICODE_REPLACEMENT_CHAR(3)" in chunks[0].quality_flags


def test_pages_are_never_merged():
    pages = [
        make_page("First page content.", page=1),
        make_page("Second page content.", page=2),
    ]

    chunks = SemanticChunker().chunk_pages(pages, "tcs_2025")

    assert len(chunks) == 2
    assert chunks[0].page_start == 1
    assert chunks[1].page_start == 2


def test_long_table_repeats_header():
    table = (
        "| Ratio | Value |\n"
        "|---|---|\n"
        "| Current ratio | 2.1 |\n"
        "| Debt-equity ratio | 0.1 |\n"
        "| Net profit ratio | 22.4% |"
    )

    page = make_page(table)

    chunks = SemanticChunker(
        max_chars=65,
        overlap_chars=10,
    ).chunk_pages([page], "tcs_2025")

    assert len(chunks) > 1

    for chunk in chunks:
        assert "| Ratio | Value |" in chunk.content
        assert "|---|---|" in chunk.content


def test_empty_page_produces_no_chunks():
    page = make_page("")

    chunks = SemanticChunker().chunk_pages([page], "tcs_2025")

    assert chunks == []


def test_oversized_agm_layout_table_pages_66_67():
    """Exact class of complex oversized AGM / e-voting layout tables as on pages 66-67."""
    cell_1 = "Shareholders registered on IDeAS facility " * 30
    cell_2 = "One-Time Password based login through depository " * 50
    oversized_row = f"|**Annexure B**|{cell_1}|{cell_2}|"
    separator = "|---|---|---|"
    table_content = f"{oversized_row}\n{separator}"

    page = make_page(
        table_content,
        page=66,
        printed=64,
        section="Notice",
        review=False,
        flags=[],
    )

    chunker = SemanticChunker(max_chars=1000, overlap_chars=100)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 1000
        assert chunk.page_start == 66
        assert chunk.printed_page == 64
        assert chunk.section == "Notice"


def test_conventional_financial_table_split_across_chunks():
    """A multi-row financial ratio table split across multiple chunks with header repeated."""
    header = "| Ratio | Current year | Previous year |\n|---|---:|---:|"
    rows = [
        "| Current ratio | 2.1 | 2.2 |",
        "| Debt-equity ratio | 0.1 | 0.1 |",
        "| Debt service coverage ratio | 23.5 | 24.0 |",
        "| Return on equity | 65.1% | 59.4% |",
        "| Trade receivables turnover | 4.4 | 4.5 |",
        "| Trade payables turnover | 3.1 | 3.1 |",
        "| Net capital turnover | 4.1 | 3.8 |",
        "| Net profit ratio | 22.4% | 21.5% |",
        "| Return on capital employed | 76.0% | 74.3% |",
        "| Return on investment | 8.5% | 8.3% |",
    ]
    full_table = header + "\n" + "\n".join(rows)

    page = make_page(
        full_table,
        page=307,
        printed=305,
        section="Standalone Financial Statements",
        review=True,
        flags=["UNICODE_REPLACEMENT_CHAR(31)", "MALFORMED_TABLE"],
    )

    # Set max_chars small enough to force 3+ chunks
    chunker = SemanticChunker(max_chars=200, overlap_chars=20)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) >= 3
    for chunk in chunks:
        assert len(chunk.content) <= 200
        assert "| Ratio | Current year | Previous year |" in chunk.content
        assert "|---|---:|---:|" in chunk.content
        assert chunk.page_start == 307
        assert chunk.printed_page == 305
        assert chunk.section == "Standalone Financial Statements"
        assert chunk.review_required is True
        assert "UNICODE_REPLACEMENT_CHAR(31)" in chunk.quality_flags


def test_single_row_larger_than_max_chars():
    """A single row larger than max_chars does not produce an oversized chunk."""
    huge_cell = "Detailed regulatory compliance disclosure item " * 40
    row = f"| Item 1 | {huge_cell} |"
    page = make_page(row, page=50)

    chunker = SemanticChunker(max_chars=300, overlap_chars=30)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 300
        assert "Detailed regulatory compliance disclosure" in chunk.content


def test_long_sentence_and_word_boundary_splitting():
    """A long sentence/text block without splitting middle of words where word-boundary exists."""
    words = ["word" + str(i) for i in range(100)]
    long_sentence = " ".join(words) + "."
    page = make_page(long_sentence, page=12)

    chunker = SemanticChunker(max_chars=120, overlap_chars=0)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.content) <= 120
        # Check that individual words are intact (not chopped in the middle)
        chunk_words = chunk.content.split()
        for w in chunk_words:
            assert w.startswith("word") or w.endswith(".")


def test_metadata_and_quality_flag_propagation_after_splitting():
    """Every chunk from a split page preserves provenance, review status, and quality flags."""
    text_block = ("Management Discussion and Analysis text block. " * 50) + "\n\n" + (
        "Operating performance review details. " * 50
    )
    page = make_page(
        text_block,
        page=42,
        printed=40,
        section="Management Discussion and Analysis",
        review=True,
        flags=["BROKEN_WORD_SPACING(4)", "MALFORMED_TABLE"],
        method="native",
    )

    chunker = SemanticChunker(max_chars=500, overlap_chars=50)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) >= 4
    for idx, chunk in enumerate(chunks, start=1):
        assert chunk.chunk_id == f"tcs_2025_p42_{idx:03d}"
        assert chunk.page_start == 42
        assert chunk.page_end == 42
        assert chunk.printed_page == 40
        assert chunk.section == "Management Discussion and Analysis"
        assert chunk.extraction_method == "native"
        assert chunk.review_required is True
        assert chunk.quality_flags == ["BROKEN_WORD_SPACING(4)", "MALFORMED_TABLE"]
        assert len(chunk.content) <= 500


def test_overlap_never_violates_max_chars_or_cuts_tables():
    """Overlap never causes size limit violations and does not corrupt tables."""
    table = (
        "| Column 1 | Column 2 |\n"
        "|---|---|\n"
        "| Val A | Val B |\n"
        "| Val C | Val D |"
    )
    text = "Introductory paragraph explaining table. " * 15
    page = make_page(f"{text}\n\n{table}", page=99)

    chunker = SemanticChunker(max_chars=350, overlap_chars=50)
    chunks = chunker.chunk_pages([page], "tcs_2025")

    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.content) <= 350
        # If chunk is table, it must have complete table rows
        if chunk.content_type == "table":
            for line in chunk.content.splitlines():
                if line.strip():
                    assert line.startswith("|") and line.endswith("|")
