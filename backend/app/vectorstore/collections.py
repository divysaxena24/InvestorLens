
"""Qdrant collection setup for InvestorLens."""

from qdrant_client import QdrantClient, models

COLLECTION_NAME = "investorlens_chunks"
VECTOR_SIZE = 384


def create_collection(client: QdrantClient) -> None:
    """Create the chunks collection if it does not already exist."""

    existing = {
        collection.name
        for collection in client.get_collections().collections
    }

    if COLLECTION_NAME in existing:
        print(f"Collection already exists: {COLLECTION_NAME}")
        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )

    print(f"Collection created: {COLLECTION_NAME}")


def main() -> None:
    client = QdrantClient(url="http://localhost:6333")

    try:
        create_collection(client)

        info = client.get_collection(COLLECTION_NAME)
        print("Vector size:", info.config.params.vectors.size)
        print("Distance:", info.config.params.vectors.distance)
        print("Points:", info.points_count)
    finally:
        client.close()


if __name__ == "__main__":
    main()
