import json
import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.core.redis import redis_client
from app.services.vectorstore_service import get_nodes_by_post_id
from app.genai.embeddings import get_embedding_model
from app.genai.vectorstore import get_vector_store
from app.genai.llm import get_llm
from app.core.config import settings
from llama_index.core import VectorStoreIndex
from llama_index.core.settings import Settings
from llama_index.core.schema import TextNode

logger = logging.getLogger(__name__)

def llm_complete(prompt: str) -> str:
    llm = get_llm()
    response = llm.complete(prompt=prompt)
    return response.text.strip()

def _find_complete_json_by_brackets(text: str, expect_array: bool) -> str:
    start_char = '[' if expect_array else '{'
    end_char = ']' if expect_array else '}'
    
    start_idx = text.find(start_char)
    if start_idx == -1:
        return None
    
    bracket_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_idx, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
        
        if not in_string:
            if char == start_char:
                bracket_count += 1
            elif char == end_char:
                bracket_count -= 1
                if bracket_count == 0:
                    return text[start_idx:i+1]
    
    return None

def _find_json_by_lines(text: str, expect_array: bool) -> str:
    lines = text.split('\n')
    
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
            
        if expect_array:
            if not (line.startswith('[') and line.endswith(']')):
                continue
        else:
            if not (line.startswith('{') and line.endswith('}')):
                continue
        
        if _is_balanced_brackets(line, expect_array):
            return line
    
    return None

def _find_json_by_regex(text: str, expect_array: bool) -> str:
    if expect_array:
        patterns = [
            r'\[[^\[\]]*\]',
            r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]',
        ]
    else:
        patterns = [
            r'\{[^{}]*\}',
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
        ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            candidate = match.group(0)
            if _is_balanced_brackets(candidate, expect_array):
                return candidate
    
    return None

def _is_balanced_brackets(text: str, expect_array: bool) -> bool:
    start_char = '[' if expect_array else '{'
    end_char = ']' if expect_array else '}'
    
    count = 0
    for char in text:
        if char == start_char:
            count += 1
        elif char == end_char:
            count -= 1
            if count < 0:
                return False
    
    return count == 0

def extract_json_from_text(text: str, expect_array: bool = False) -> any:
    logger = logging.getLogger(__name__)
    
    if not text or not text.strip():
        logger.error("Empty or invalid text provided")
        raise ValueError("Empty or invalid text provided")
    
    text = text.strip()
    logger.debug(f"Attempting to extract JSON {'array' if expect_array else 'object'} from text: {text[:100]}...")
    
    strategies = [
        ("bracket counting", lambda: _find_complete_json_by_brackets(text, expect_array)),
        ("line-by-line", lambda: _find_json_by_lines(text, expect_array)),
        ("regex", lambda: _find_json_by_regex(text, expect_array))
    ]
    
    for strategy_name, strategy_func in strategies:
        try:
            json_str = strategy_func()
            if json_str:
                logger.debug(f"Strategy '{strategy_name}' found JSON: {json_str[:100]}...")
                result = json.loads(json_str)
                logger.debug(f"Successfully parsed JSON using '{strategy_name}' strategy")
                return result
        except json.JSONDecodeError as e:
            logger.debug(f"Strategy '{strategy_name}' found JSON but failed to parse: {e}")
        except Exception as e:
            logger.debug(f"Strategy '{strategy_name}' failed: {e}")
    
    logger.error("All strategies failed to extract valid JSON")
    raise ValueError(f"No valid JSON {'array' if expect_array else 'object'} found in text")

def validate_response_structure(result: Any, expected_keys: List[str], fallback: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(result, dict):
        logger.warning("Response is not a dictionary, using fallback")
        return fallback
    
    missing_keys = [key for key in expected_keys if key not in result]
    if missing_keys:
        logger.warning(f"Missing keys in response: {missing_keys}, using fallback")
        return fallback
    
    return result

def safe_llm_call(prompt: str, expect_array: bool = False, fallback: Any = None) -> Any:
    try:
        text = llm_complete(prompt)
        result = extract_json_from_text(text, expect_array=expect_array)
        return result
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return fallback

def get_cached_chunks(post_id: int) -> Optional[List[str]]:
    try:
        chunks_json = redis_client.get(f"post:{post_id}:chunks")
        if chunks_json:
            logger.info(f"Found chunks in Redis for post {post_id}")
            return json.loads(chunks_json)
    except Exception as e:
        logger.warning(f"Failed to get cached chunks for post {post_id}: {e}")
    return None

def cache_chunks(post_id: int, chunks: List[str]) -> None:
    try:
        redis_client.set(f"post:{post_id}:chunks", json.dumps(chunks))
        logger.info(f"Cached chunks in Redis for post {post_id}")
    except Exception as e:
        logger.warning(f"Failed to cache chunks for post {post_id}: {e}")

def get_nodes_from_qdrant(post_id: int) -> List[TextNode]:
    try:
        nodes = get_nodes_by_post_id(post_id)
        if not nodes:
            logger.error(f"No chunks found for post {post_id} in QdrantDB")
            raise ValueError("No chunks found for this post in QDrantDB.")
        return nodes
    except AttributeError:
        logger.error(f"No chunks found for post {post_id} in QdrantDB (AttributeError)")
        raise ValueError("No chunks found for this post in QDrantDB.")

def create_text_nodes(chunks: List[str], post_id: int) -> List[TextNode]:
    return [
        TextNode(text=chunk, metadata={"post_id": post_id, "chunk_index": idx})
        for idx, chunk in enumerate(chunks)
    ]

def retrieve_relevant_chunks(nodes: List[TextNode], question: str, top_k: int) -> List[str]:
    vector_store = get_vector_store()
    embed_model = get_embedding_model()
    Settings.embed_model = embed_model
    
    index = VectorStoreIndex(nodes=nodes, vector_store=vector_store)
    retriever = index.as_retriever(similarity_top_k=top_k)
    retrieved_nodes = retriever.retrieve(question)
    
    top_chunks = [node.text for node in retrieved_nodes]
    logger.info(f"Retrieved top {len(top_chunks)} chunks for Q&A")
    return top_chunks

def cache_qa_result(post_id: int, question: str, result: Dict[str, Any]) -> None:
    cache_key = f"post:{post_id}:qa:{question}"
    try:
        redis_client.set(cache_key, json.dumps(result), ex=3600)
        logger.info(f"Cached Q&A result for post {post_id}")
    except Exception as e:
        logger.warning(f"Failed to cache Q&A result: {e}")

def get_cached_qa_result(post_id: int, question: str) -> Optional[Dict[str, Any]]:
    cache_key = f"post:{post_id}:qa:{question}"
    try:
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"Cache hit for Q&A: post_id={post_id}, question='{question}'")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Failed to get cached Q&A result: {e}")
    return None

def get_post_chunks(post_id: int) -> List[str]:
    chunks = get_cached_chunks(post_id)
    if chunks is None:
        nodes = get_nodes_from_qdrant(post_id)
        chunks = [node.text for node in nodes]
        cache_chunks(post_id, chunks)
    return chunks

def convert_citation_indices_to_text(citations: List[int], top_chunks: List[str]) -> List[str]:
    return [
        top_chunks[i-1] for i in citations 
        if 1 <= i <= len(top_chunks)
    ]

def search_vector_database(question: str, top_k: int) -> List[Any]:
    embed_model = get_embedding_model()
    question_embedding = embed_model.get_text_embedding(question)
    
    vector_store = get_vector_store()
    results = vector_store._client.query_points(
        collection_name=settings.QDRANT_COLLECTION,
        query=question_embedding,
        with_payload=True,
        limit=top_k * 2
    ).points
    
    return results

def parse_vector_results(results: List[Any]) -> Tuple[List[TextNode], set]:
    retrieved_nodes = []
    relevant_post_ids = set()
    
    for point in results:
        try:
            node_content = json.loads(point.payload["_node_content"])
            chunk_text = node_content.get("text", "")
            metadata = node_content.get("metadata", {})
            
            if chunk_text:
                node = TextNode(text=chunk_text, metadata=metadata)
                retrieved_nodes.append(node)
                
                if 'post_id' in metadata:
                    relevant_post_ids.add(metadata['post_id'])
        except Exception as e:
            logger.warning(f"Could not parse node content: {e}")
            continue
    
    return retrieved_nodes, relevant_post_ids

def create_rag_query_engine(nodes: List[TextNode], top_k: int):
    embed_model = get_embedding_model()
    Settings.embed_model = embed_model
    
    temp_index = VectorStoreIndex(nodes=nodes)
    query_engine = temp_index.as_query_engine(
        similarity_top_k=min(top_k, len(nodes)),
        response_mode="compact",
        llm=get_llm(),
        streaming=False,
        structured_answer_filtering=True
    )
    return query_engine

def prepare_context_with_posts(nodes: List[TextNode], top_k: int) -> str:
    context_with_posts = []
    for i, node in enumerate(nodes[:top_k]):
        if hasattr(node, 'text') and node.text:
            post_id = node.metadata.get('post_id', 'unknown') if hasattr(node, 'metadata') else 'unknown'
            context_with_posts.append(f"[Post {post_id}]: {node.text}")
    
    return "\n---\n".join(context_with_posts) 