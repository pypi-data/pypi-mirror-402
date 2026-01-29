"""
Vector search tool for semantic document retrieval.
Simplified from Parlant version - plain async function.
"""

from pymongo import AsyncMongoClient
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


async def embed_text(text: str) -> list[float]:
    """Generate embeddings for text using Gemini API."""
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    
    result = genai.embed_content(
        model="gemini-embedding-001",
        content=text,
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=1536
    )
    return result['embedding']


async def vector_search(query: str, limit: int = 5, similarity_threshold: float = 0.7) -> list[dict]:
    """
    Search for semantically similar documents using vector embeddings.
    
    Args:
        query: Search query text
        limit: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1) to include a document
    
    Returns:
        List of matching documents with content, source, and similarity score
    """
    try:
        # Generate query embedding
        query_embedding = await embed_text(query)
        
        # Connect to MongoDB
        conn_string = os.getenv("MONGO_CONNECTION_STRING")
        if not conn_string:
            return []
        
        client = AsyncMongoClient(conn_string)
        db = client["stockdb"]
        collection = db["vector_documents"]

        # MongoDB Atlas Vector Search pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embeddings",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 20,
                    "limit": limit
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "id": 1,
                    "createdAt": 1,
                    "source": 1,
                    "text": 1,
                    "metadata": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]

        cursor = await collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Filter by similarity threshold
        filtered_results = [r for r in results if r.get("score", 0.0) >= similarity_threshold]
        
        # Format response
        return [
            {
                "content": doc.get("text", ""),
                "id": doc.get("id"),
                "source": doc.get("source"),
                "similarity_score": doc.get("score", 0.0),
                "metadata": doc.get("metadata", {}),
            }
            for doc in filtered_results
        ]

    except Exception as e:
        return []
