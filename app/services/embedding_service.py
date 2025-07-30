from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.services.vectorstore_service import delete_points_by_post_id
from app.core.redis import redis_client
from llama_index.core.schema import TextNode
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from app.utils.constants import CHUNK_SIZE
import json
import logging

logger = logging.getLogger(__name__)


def embed_and_store_post(post_id: int, post_content: str):
    logger.info(f"Embedding and storing post {post_id}")
    try:
        chunks = [post_content[i:i+CHUNK_SIZE] for i in range(0, len(post_content), CHUNK_SIZE)] 
        nodes = [
            TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
            for idx, chunk in enumerate(chunks)
        ]
        vector_store = get_vector_store()
        embed_model = get_embedding_model()
        Settings.embed_model = embed_model
        index = VectorStoreIndex.from_vector_store(vector_store)
        index.insert_nodes(nodes)
        redis_client.set(f"post:{post_id}:chunks", json.dumps(chunks))
        logger.info(f"Successfully embedded and stored post {post_id} with {len(chunks)} chunks.")
    except Exception as e:
        logger.error(f"Failed to embed and store post {post_id}: {e}")
        raise


def delete_post_embeddings(post_id: int):
    logger.info(f"Deleting embeddings and cache for post {post_id}")
    try:
        deleted_count = delete_points_by_post_id(post_id)
        
        if deleted_count > 0:
            logger.info(f"Successfully deleted {deleted_count} points for post {post_id}")
        else:
            logger.warning(f"No points found for post {post_id}")
        
        redis_client.delete(f"post:{post_id}:chunks")
        logger.info(f"Successfully deleted embeddings and cache for post {post_id}")
    except Exception as e:
        logger.error(f"Failed to delete embeddings/cache for post {post_id}: {e}")
        raise
