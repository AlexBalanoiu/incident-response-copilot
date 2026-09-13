from chromadb import Documents, EmbeddingFunction, Embeddings
import litellm

EMBEDDING_MODEL = "gemini/gemini-embedding-001"


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __call__(self, input: Documents) -> Embeddings:
        response = litellm.embedding(model=EMBEDDING_MODEL, input=input)
        return [item["embedding"] for item in response["data"]]