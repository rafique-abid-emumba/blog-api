import logging
from typing import Any, Dict, List
from app.genai.utils import (
    validate_response_structure,
    safe_llm_call,
    create_text_nodes,
    retrieve_relevant_chunks,
    cache_qa_result,
    get_cached_qa_result,
    search_vector_database,
    parse_vector_results,
    create_rag_query_engine,
    prepare_context_with_posts,
    get_post_chunks,
    convert_citation_indices_to_text
)
from app.genai.prompts import (
    get_title_tags_prompt,
    get_summary_prompt,
    get_qa_prompt,
    get_comment_analysis_prompt,
    get_trending_tags_prompt,
    get_citation_extraction_prompt
)

logger = logging.getLogger(__name__)

def suggest_title_and_tags(post_content: str) -> Dict[str, Any]:
    """Suggests a title and tags for a blog post using GenAI."""
    logger.info("Suggesting title and tags for post content")
    
    fallback_response = {
        "title": "Untitled Post",
        "tags": ["general", "blog"]
    }
    
    prompt = get_title_tags_prompt(post_content)
    result = safe_llm_call(prompt, fallback=fallback_response)
    
    if result == fallback_response:
        return fallback_response
    
    result = validate_response_structure(result, ["title", "tags"], fallback_response)
    
    if not result.get('title') or len(result['title']) > 60:
        result['title'] = fallback_response['title']
    
    if not result.get('tags') or not isinstance(result['tags'], list):
        result['tags'] = fallback_response['tags']
    
    logger.info("Successfully suggested title and tags")
    return result

def summarize_post(post_content: str) -> Dict[str, Any]:
    """Summarizes a blog post using GenAI."""
    logger.info("Summarizing post content")
    
    fallback_response = {
        "summary": "This post discusses various topics and provides insights on the subject matter.",
        "citations": ["Content analysis"]
    }
    
    prompt = get_summary_prompt(post_content)
    result = safe_llm_call(prompt, fallback=fallback_response)
    
    if result == fallback_response:
        return fallback_response
    
    result = validate_response_structure(result, ["summary", "citations"], fallback_response)
    
    if not result.get('summary') or len(result['summary']) > 500:
        result['summary'] = fallback_response['summary']
    
    if not result.get('citations') or not isinstance(result['citations'], list):
        result['citations'] = fallback_response['citations']
    
    logger.info("Successfully summarized post")
    return result

def answer_question_about_post(post_id: int, question: str, top_k: int = 3) -> Dict[str, Any]:
    """Answers a question about a blog post using RAG."""
    cached_result = get_cached_qa_result(post_id, question)
    if cached_result:
        return cached_result
    
    logger.info(f"Cache miss for Q&A: post_id={post_id}, question='{question}'")
    
    fallback_response = {
        "answer": "I cannot find specific information to answer this question based on the available content.",
        "citations": []
    }
    
    try:
        
        chunks = get_post_chunks(post_id)
        nodes = create_text_nodes(chunks, post_id)
        top_chunks = retrieve_relevant_chunks(nodes, question, top_k)
        
        if not top_chunks:
            logger.warning("No relevant chunks found for question")
            return fallback_response
        
        context = "\n---\n".join(top_chunks)
        prompt = get_qa_prompt(context, question)
        result = safe_llm_call(prompt, fallback=fallback_response)
        
        if result == fallback_response:
            return fallback_response
        
        result = validate_response_structure(result, ["answer", "citations"], fallback_response)
        
        if result.get("citations"):
            result["citations"] = convert_citation_indices_to_text(result.get("citations", []), top_chunks)
        
        cache_qa_result(post_id, question, result)
        
        return result
    except Exception as e:
        logger.error(f"Error in answer_question_about_post: {e}")
        raise

def answer_question_global(question: str, top_k: int = 5) -> Dict[str, Any]:
    """Answers a question using RAG across all content in the vector database."""
    logger.info(f"Answering global question: '{question[:50]}...'")
    
    fallback_response = {
        "answer": "I cannot find specific information to answer this question based on the available content.",
        "citations": []
    }
    
    try:
        results = search_vector_database(question, top_k)
        
        if not results:
            logger.warning("No content found in vector database")
            return {
                "answer": "No content is available in the vector database to answer this question.",
                "citations": []
            }
        
        retrieved_nodes, relevant_post_ids = parse_vector_results(results)
        
        if not retrieved_nodes:
            logger.warning("No valid nodes found in vector database")
            return {
                "answer": "No valid content is available in the vector database to answer this question.",
                "citations": []
            }
        
        logger.info(f"Retrieved {len(retrieved_nodes)} nodes from {len(relevant_post_ids)} posts")
        
        query_engine = create_rag_query_engine(retrieved_nodes, top_k)
        rag_response = query_engine.query(question)
        rag_answer = str(rag_response)
        
        context = prepare_context_with_posts(retrieved_nodes, top_k)
        
        logger.info("Extracting citations with post tracking")
        prompt = get_citation_extraction_prompt(rag_answer, context)
        result = safe_llm_call(prompt, fallback=fallback_response)
        
        if result == fallback_response:
            return fallback_response
        
        result = validate_response_structure(result, ["answer", "citations"], fallback_response)
        
        logger.info(f"Successfully answered global question with {len(result.get('citations', []))} citations")
        return result
    except Exception as e:
        logger.error(f"Error in answer_question_global: {e}")
        return fallback_response

def analyze_comment_sentiment(comment: str) -> dict:
    """Analyze a comment for both sentiment and abuse detection."""
    logger.info(f"Analyzing comment for sentiment and abuse: '{comment[:50]}...'")
    
    fallback_response = {
        "sentiment": "neutral",
        "is_abusive": False
    }
    
    prompt = get_comment_analysis_prompt(comment)
    result = safe_llm_call(prompt, fallback=fallback_response)
    
    if result == fallback_response:
        return fallback_response
    
    result = validate_response_structure(result, ["sentiment", "is_abusive"], fallback_response)
    
    if result.get('sentiment') not in ['positive', 'negative', 'neutral']:
        result['sentiment'] = fallback_response['sentiment']
    
    if not isinstance(result.get('is_abusive'), bool):
        result['is_abusive'] = fallback_response['is_abusive']
    
    logger.info(f"Comment analysis result: sentiment='{result['sentiment']}', abusive={result['is_abusive']}")
    return result

def suggest_trending_tags(posts_with_comments: List[dict], top_k: int = 10) -> List[str]:
    """Analyze recent posts and their comments to suggest trending tags."""
    logger.info(f"Analyzing {len(posts_with_comments)} posts for trending tags")
    
    fallback_response = ["general", "blog", "discussion"]
    
    prompt = get_trending_tags_prompt(posts_with_comments, top_k)
    result = safe_llm_call(prompt, expect_array=True, fallback=fallback_response)
    
    if result == fallback_response:
        return fallback_response[:top_k]
    
    if not isinstance(result, list) or not all(isinstance(tag, str) for tag in result):
        logger.warning("Invalid response structure, using fallback")
        return fallback_response[:top_k]
    
    result = result[:top_k]
    logger.info(f"Successfully identified {len(result)} trending tags: {result}")
    return result