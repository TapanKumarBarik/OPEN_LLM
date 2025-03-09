from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts)
        return embeddings.tolist()
    
    def similarity_search(self, query: str, embeddings: List[List[float]], top_k: int = 5) -> List[int]:
        query_embedding = self.model.encode([query])[0]
        similarities = np.dot(embeddings, query_embedding)
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return top_indices.tolist()