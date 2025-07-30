from app.core.config import settings

def get_embedding_model():
    if getattr(settings, "EMBEDDING_PROVIDER", None) == "cohere":
        from llama_index.embeddings.cohere import CohereEmbedding
        return CohereEmbedding(api_key=settings.COHERE_API_KEY)
    else:
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2") 