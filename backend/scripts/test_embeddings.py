
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    model = SentenceTransformer(MODEL_NAME, device="cpu")

    sentences = [
        "TCS revenue increased during FY2025.",
        "The company's annual sales grew in 2025.",
        "The weather is pleasant today.",
    ]

    embeddings = model.encode(
        sentences,
        convert_to_tensor=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    print("Embedding shape:", embeddings.shape)

    similarity = cos_sim(embeddings, embeddings)

    print("\nCosine similarity matrix:")
    print(similarity)

    print("\nFinancial sentence similarity:")
    print(round(similarity[0][1].item(), 4))

    print("\nUnrelated sentence similarity:")
    print(round(similarity[0][2].item(), 4))


if __name__ == "__main__":
    main()
