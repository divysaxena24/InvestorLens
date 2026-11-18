
import pytest

from app.ingestion.embeddings import EmbeddingGenerator


@pytest.fixture(scope="module")
def generator():
    return EmbeddingGenerator(device="cpu")


def test_embedding_dimension(generator):
    vectors = generator.generate(["TCS revenue increased in FY2025."])

    assert len(vectors) == 1
    assert len(vectors[0]) == 384


def test_embeddings_are_normalized(generator):
    vectors = generator.generate(["Annual revenue increased."])

    norm = sum(value**2 for value in vectors[0]) ** 0.5

    assert norm == pytest.approx(1.0, abs=1e-5)


def test_multiple_texts(generator):
    texts = [
        "TCS revenue increased.",
        "Operating profit improved.",
        "Cash flow remained stable.",
    ]

    vectors = generator.generate(texts)

    assert len(vectors) == 3
    assert all(len(vector) == 384 for vector in vectors)


def test_empty_input_returns_empty_list(generator):
    assert generator.generate([]) == []


def test_blank_text_raises_error(generator):
    with pytest.raises(ValueError):
        generator.generate(["TCS revenue", "   "])


def test_embed_chunks_preserves_metadata(generator):
    from app.ingestion.chunker import DocumentChunk

    chunk = DocumentChunk(
        chunk_id="tcs_2025_p1_001",
        document_id="tcs_2025",
        content="TCS revenue increased in FY2025.",
        page_start=1,
        page_end=1,
        printed_page=1,
        section="Financial Highlights",
        content_type="text",
        extraction_method="native",
        review_required=True,
        quality_flags=["UNICODE_REPLACEMENT_CHAR(2)"],
    )

    result = generator.embed_chunks([chunk])

    assert len(result) == 1
    assert result[0]["chunk_id"] == chunk.chunk_id
    assert result[0]["document_id"] == chunk.document_id
    assert result[0]["page_start"] == 1
    assert result[0]["section"] == "Financial Highlights"
    assert result[0]["review_required"] is True
    assert result[0]["quality_flags"] == ["UNICODE_REPLACEMENT_CHAR(2)"]
    assert len(result[0]["vector"]) == 384
