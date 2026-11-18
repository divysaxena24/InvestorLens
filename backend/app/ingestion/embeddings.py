
"""Embedding generation for InvestorLens document chunks."""

from sentence_transformers import SentenceTransformer

from app.ingestion.chunker import DocumentChunk


class EmbeddingGenerator:
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    def __init__(self, device: str = "cpu") -> None:
        self.model = SentenceTransformer(
            self.MODEL_NAME,
            device=device,
        )

        actual_dimension = self.model.get_embedding_dimension()

        if actual_dimension != self.EMBEDDING_DIMENSION:
            raise ValueError(
                f"Expected {self.EMBEDDING_DIMENSION} dimensions, "
                f"got {actual_dimension}"
            )

    def generate(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if any(not text.strip() for text in texts):
            raise ValueError("Embedding input cannot contain empty text")

        embeddings = self.model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return embeddings.tolist()

    def embed_chunks(
        self,
        chunks: list[DocumentChunk],
    ) -> list[dict]:
        texts = [chunk.content for chunk in chunks]
        vectors = self.generate(texts)

        return [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "vector": vector,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "printed_page": chunk.printed_page,
                "section": chunk.section,
                "content_type": chunk.content_type,
                "review_required": chunk.review_required,
                "quality_flags": chunk.quality_flags,
            }
            for chunk, vector in zip(chunks, vectors)
        ]
