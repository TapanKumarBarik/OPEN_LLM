from .search.azure_search_service import AzureSearchService
from typing import Dict, List

class VectorStore:
    def __init__(self):
        self.search_service = AzureSearchService.get_instance()
    
    def similarity_search(self, query: str, user_id: int, filters: Dict = None, k: int = 10):
        return self.search_service.similarity_search(query, user_id, filters, k)