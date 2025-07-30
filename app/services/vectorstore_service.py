from app.genai.vectorstore import get_vector_store
from app.core.config import settings
from qdrant_client.http import models
from llama_index.core.schema import TextNode
import logging
import json

logger = logging.getLogger(__name__)

def get_points_by_post_id(post_id: int, with_payload: bool = True):
   
    try:
        vector_store = get_vector_store()
        collection_name = settings.QDRANT_COLLECTION
        filter = models.Filter(
            must=[
                models.FieldCondition(key="post_id", match=models.MatchValue(value=post_id))
            ]
        )
        collection_info = vector_store._client.get_collection(collection_name)
        vector_size = collection_info.config.params.vectors.size
        results = vector_store._client.query_points(
            collection_name=collection_name,
            query=[0.0] * vector_size,
            query_filter=filter,
            with_payload=with_payload,
            limit=1000
        ).points
        
        logger.info(f"Fetched {len(results)} points for post_id {post_id} from Qdrant.")
        return results
    except Exception as e:
        logger.error(f"Error fetching points for post_id {post_id} from Qdrant: {e}")
        raise

def get_nodes_by_post_id(post_id: int):
    try:
        results = get_points_by_post_id(post_id, with_payload=True)
        
        chunks = [json.loads(point.payload["_node_content"]).get("text", "") for point in results]
        nodes = [
            TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
            for idx, chunk in enumerate(chunks)
        ]
        
        logger.info(f"Fetched {len(nodes)} nodes for post_id {post_id} from Qdrant.")
        return nodes
    except Exception as e:
        logger.error(f"Error fetching nodes for post_id {post_id} from Qdrant: {e}")
        raise

def delete_points_by_post_id(post_id: int):
    try:
        results = get_points_by_post_id(post_id, with_payload=False)
        
        if results:
            point_ids = [point.id for point in results]
            vector_store = get_vector_store()
            
            vector_store._client.delete(
                collection_name=settings.QDRANT_COLLECTION,
                points_selector=point_ids
            )
            logger.info(f"Deleted {len(point_ids)} points for post {post_id}")
            return len(point_ids)
        else:
            logger.warning(f"No points found for post {post_id}")
            return 0
    except Exception as e:
        logger.error(f"Error deleting points for post_id {post_id} from Qdrant: {e}")
        raise
