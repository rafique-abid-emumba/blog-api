from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.core.redis import redis_client
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
import json

def embed_and_store_post(post_id: int, post_content: str):
    chunks = [post_content[i:i+500] for i in range(0, len(post_content), 500)]
    nodes = [
        TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
        for idx, chunk in enumerate(chunks)
    ]
    vector_store = get_vector_store()
    embed_model = get_embedding_model()
    Settings.embed_model = embed_model
    index = VectorStoreIndex(nodes=[], vector_store=vector_store)
    index.insert_nodes(nodes)
    redis_client.set(f"post:{post_id}:chunks", json.dumps(chunks))

def delete_post_embeddings(post_id: int):
    vector_store = get_vector_store()
    vector_store.delete(metadata_filter={"post_id": post_id})
    redis_client.delete(f"post:{post_id}:chunks") 