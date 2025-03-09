from sqlalchemy import text
from sentence_transformers import SentenceTransformer
from app import db
from app.models.document_chunk import DocumentChunk
import numpy as np
from typing import List, Dict

class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def similarity_search(self, query: str, filters: Dict = None, k: int = 10):
        try:
            # Encode and normalize query
            query_embedding = self.model.encode(query)
            query_embedding = np.array(query_embedding)
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Use explicit cast to vector type in PostgreSQL
            base_query = text("""
                SELECT *, 
                (1 - (embedding <-> :query_embedding::vector)) as cosine_similarity 
                FROM document_chunk
                WHERE 1=1
            """)
            
            params = {"query_embedding": query_embedding.tolist()}
            
            # Handle filters correctly
            if filters and 'document_id' in filters:
                if isinstance(filters['document_id'], dict) and '$in' in filters['document_id']:
                    doc_ids = filters['document_id']['$in']
                    base_query = text(base_query.text + " AND document_id = ANY(:doc_ids)")
                    params['doc_ids'] = doc_ids
                elif isinstance(filters['document_id'], list):
                    base_query = text(base_query.text + " AND document_id = ANY(:doc_ids)")
                    params['doc_ids'] = filters['document_id']
                else:
                    base_query = text(base_query.text + " AND document_id = :doc_id")
                    params['doc_id'] = filters['document_id']
            
            base_query = text(base_query.text + """
                ORDER BY cosine_similarity DESC
                LIMIT :limit
            """)
            params['limit'] = k
            
            results = db.session.execute(base_query, params).all()
            
            chunks = []
            for result in results:
                chunk = DocumentChunk(
                    id=result.id,
                    document_id=result.document_id,
                    user_id=result.user_id,
                    content=result.content,
                    chunk_metadata=result.chunk_metadata,
                    created_at=result.created_at
                )
                chunks.append(chunk)
            
            return chunks
        except Exception as e:
            print(f"Error in similarity search: {str(e)}")
            raise