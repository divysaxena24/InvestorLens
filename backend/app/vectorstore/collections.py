
from qdrant_client import QdrantClient, models

from app.core.config import settings

COLLECTION_NAME = settings.QDRANT_COLLECTION
VECTOR_SIZE = 384


def create_collection(client: QdrantClient) -> None:
    """Create the collection if missing; otherwise validate its configuration."""

    existing = {
        collection.name
        for collection in client.get_collections().collections
    }

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
        print(f"Collection created: {COLLECTION_NAME}")
        return

    info = client.get_collection(COLLECTION_NAME)
    vector_config = info.config.params.vectors

    if not isinstance(vector_config, models.VectorParams):
        raise ValueError("Expected a single unnamed vector configuration.")

    if vector_config.size != VECTOR_SIZE:
        raise ValueError(
            f"Expected {VECTOR_SIZE} dimensions, got {vector_config.size}."
        )

    if vector_config.distance != models.Distance.COSINE:
        raise ValueError("Collection must use Cosine distance.")

    print(f"Collection validated: {COLLECTION_NAME}")


def main() -> None:
    from app.vectorstore.client import get_qdrant_client

    client = get_qdrant_client()

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
