from typing import List, Dict

def get_title_tags_prompt(post_content: str) -> str:
    """Generate prompt for title and tags suggestion."""
    return f"""# INSTRUCTION: Generate Title and Tags

You are an AI assistant that generates catchy titles and relevant tags for blog posts.

## TASK:
Analyze the following blog post content and generate:
1. A concise, catchy title (max 60 characters)
2. 3-5 relevant tags that describe the main topics

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "title": "Your suggested title here",
    "tags": ["tag1", "tag2", "tag3"]
}}

## IMPORTANT RULES:
- If you cannot generate a proper title, use "Untitled Post"
- If you cannot generate tags, use ["general", "blog"]
- Never include explanations, markdown, or extra text
- Only return the JSON object

## BLOG POST CONTENT:
{post_content}

## RESPONSE:"""

def get_summary_prompt(post_content: str) -> str:
    """Generate prompt for post summarization."""
    return f"""# INSTRUCTION: Summarize Blog Post

You are an AI assistant that creates concise summaries of blog posts.

## TASK:
Create a 2-3 sentence summary of the following blog post that captures the main points.
Also identify key phrases or concepts from the original text that support your summary.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "summary": "Your 2-3 sentence summary here",
    "citations": ["key phrase 1", "key phrase 2"]
}}

## IMPORTANT RULES:
- If you cannot generate a proper summary, use "This post discusses various topics and provides insights on the subject matter."
- If you cannot identify citations, use ["Content analysis"]
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Summary should be 2-3 sentences maximum

## BLOG POST CONTENT:
{post_content}

## RESPONSE:"""

def get_qa_prompt(context: str, question: str) -> str:
    """Generate prompt for Q&A about a specific post."""
    return f"""# INSTRUCTION: Answer Question About Blog Post

You are an AI assistant that answers questions about blog posts using only the provided context.

## TASK:
Answer the given question using ONLY the information from the provided context.
Cite the specific chunks (by number) that support your answer.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "answer": "Your answer based on the context",
    "citations": [1, 2, 3]
}}

## IMPORTANT RULES:
- Only use information from the provided context
- If the context doesn't contain relevant information, use "I cannot find specific information to answer this question based on the available content."
- If you cannot identify citations, use []
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Citations should be chunk numbers (1, 2, 3, etc.)

## CONTEXT (Chunks from blog post):
{context}

## QUESTION:
{question}

## RESPONSE:"""

def get_comment_analysis_prompt(comment: str) -> str:
    """Generate prompt for comment sentiment and abuse analysis."""
    return f"""# INSTRUCTION: Analyze Comment Sentiment and Abuse

You are an AI assistant that analyzes comments for sentiment and potential abuse.

## TASK:
Analyze the following comment and determine:
1. Sentiment: positive, negative, or neutral
2. Whether the comment contains abusive content

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "sentiment": "positive|negative|neutral",
    "is_abusive": true|false
}}

## IMPORTANT RULES:
- If you cannot determine sentiment, use "neutral"
- If you cannot determine abuse, use false
- Never include explanations, markdown, or extra text
- Only return the JSON object
- Sentiment must be exactly: "positive", "negative", or "neutral"
- is_abusive must be exactly: true or false

## COMMENT TO ANALYZE:
{comment}

## RESPONSE:"""

def get_trending_tags_prompt(posts_with_comments: List[Dict], top_k: int) -> str:
    """Generate prompt for trending tags analysis."""
    prompt = f"""# INSTRUCTION: Identify Trending Tags

You are an AI assistant that identifies trending topics from blog posts and comments.

## TASK:
Analyze the following recent blog posts and their comments to identify the top {top_k} trending tags.
Consider both explicit tags mentioned and implicit topics discussed.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON array of strings in this exact format:
["tag1", "tag2", "tag3"]

## IMPORTANT RULES:
- If you cannot identify trending tags, use ["general", "blog", "discussion"]
- Never include explanations, markdown, or extra text
- Only return the JSON array
- Maximum {top_k} tags
- Tags should be lowercase, single words or short phrases

## RECENT CONTENT:
"""
    
    for i, post_data in enumerate(posts_with_comments, 1):
        prompt += f"{i}. Post Title: {post_data['title']}\n"
        prompt += f"   Content: {post_data['content'][:500]}...\n"
        prompt += f"   Tags: {', '.join(post_data.get('tags', []))}\n"
        if post_data.get('comments'):
            prompt += f"   Top Comments ({len(post_data['comments'])}):\n"
            for j, comment in enumerate(post_data['comments'][:5], 1):
                prompt += f"     {j}. {comment['content'][:200]}...\n"
        prompt += "\n"
    
    prompt += f"""## RESPONSE:"""
    return prompt

def get_citation_extraction_prompt(rag_answer: str, context: str) -> str:
    """Generate prompt for extracting citations with post tracking."""
    return f"""# INSTRUCTION: Extract Citations with Post Tracking

You are an AI assistant that extracts relevant citations from RAG responses and tracks which post each citation comes from.

## TASK:
Given the RAG answer and the context with post IDs, extract relevant citations and identify which post each citation comes from.

## OUTPUT FORMAT:
You must respond with ONLY a valid JSON object in this exact format:
{{
    "answer": "The RAG answer or fallback message if hallucinated",
    "citations": [
        {{
            "text": "relevant quote from context",
            "post_id": 123
        }},
        {{
            "text": "another relevant quote from context",
            "post_id": 456
        }}
    ]
}}

## CRITICAL FORMAT RULES:
- post_id must be a NUMBER (integer), not a string
- Use only the numeric part from the context (e.g., from "[Post 2]" use 2, not "Post2")
- Never use strings like "Post2" or "Post 2" for post_id
- post_id must be a valid integer

## IMPORTANT RULES:
- ALWAYS check for hallucination before using RAG answer
- ONLY extract citations from the provided context
- ONLY use post IDs that are actually present in the context
- If the context doesn't contain relevant information, use empty citations array
- If RAG answer claims information but has no citations, replace with fallback message
- Never include explanations, markdown, or extra text
- Only return the JSON object

## RAG ANSWER:
{rag_answer}

## CONTEXT WITH POST IDs:
{context}

## RESPONSE:""" 