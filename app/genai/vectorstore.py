from app.core.config import settings
from qdrant_client import QdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore

def get_vector_store():
    
    client = QdrantClient(
        host=settings.QDRANT_HOST,
        port=settings.QDRANT_PORT,
        api_key=settings.QDRANT_API_KEY or None
    )
    return QdrantVectorStore(
        client=client,
        collection_name=settings.QDRANT_COLLECTION
    ) 