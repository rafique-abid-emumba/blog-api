from app.core.config import settings

def get_vector_store():
    if getattr(settings, "VECTOR_DB_PROVIDER", None) == "qdrant":
        from qdrant_client import QdrantClient
        from llama_index.vector_stores.qdrant import QdrantVectorStore
        client = QdrantClient(host=settings.QDRANT_HOST, api_key=settings.QDRANT_API_KEY)
        return QdrantVectorStore(client=client, collection_name="blog_posts")
    else:
        import chromadb
        from llama_index.vector_stores.chroma import ChromaVectorStore
        chroma_client = chromadb.PersistentClient(path="./chroma_db")
        return ChromaVectorStore(chroma_collection=chroma_client.get_or_create_collection("blog_posts")) 