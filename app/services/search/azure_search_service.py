from typing import List, Optional, Dict
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (  
    SearchIndex,  
    SimpleField,  
    SearchField,  
    SearchableField,  
    SearchFieldDataType,  
    VectorSearch,  
    VectorSearchProfile,  
    HnswAlgorithmConfiguration,  
    HnswParameters  
)  
import os

import json
from ..embedding.embedding_service import EmbeddingService

class AzureSearchService:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "document-chunks")
        
        self.credential = AzureKeyCredential(self.key)
        self.index_client = SearchIndexClient(endpoint=self.endpoint, credential=self.credential)
        self.search_client = SearchClient(endpoint=self.endpoint, 
                                        index_name=self.index_name, 
                                        credential=self.credential)
        
        self.embedding_service = EmbeddingService()
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        if not self._index_exists():
            self._create_index()
    
    def _index_exists(self) -> bool:
        try:
            self.index_client.get_index(self.index_name)
            return True
        except Exception:
            return False
        
            
    def _create_index(self):
        
        index_schema = SearchIndex(  
        name=self.index_name,  
        fields = [
            SearchField(name="id", type=SearchFieldDataType.String, key=True),
            SearchField(name="document_id", type=SearchFieldDataType.Int64),
            SearchField(name="user_id", type=SearchFieldDataType.Int64),
            SearchField(name="content", type=SearchFieldDataType.String, searchable=True),
            SearchField(name="chunk_metadata", type=SearchFieldDataType.String,searchable=True),
            SearchField(
                name="embedding",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=384,
                vector_search_profile_name="myHnswProfile"
            )
        ],
        vector_search=VectorSearch(  
            algorithms=[  
                HnswAlgorithmConfiguration(  
                    name="default",  
                    parameters=HnswParameters(  
                        m=4,  # Number of bi-directional links  
                        ef_construction=400,  # Size of dynamic candidate list for construction  
                        ef_search=500,  # Size of dynamic candidate list for search  
                        metric="cosine"  # Distance metric  
                    )  
                )  
            ],  
            profiles=[  
                VectorSearchProfile(  
                    name="myHnswProfile",  
                    algorithm_configuration_name="default"  
                )  
            ]  
        )

        )

        self.index_client.create_index(index_schema)

    
    def index_documents(self, chunks: List[Dict]):
        documents = []
        for chunk in chunks:
            embedding = self.embedding_service.create_embeddings([chunk['content']])[0]
            doc = {
                "id": f"{chunk['document_id']}_{chunk['id']}",
                "document_id": chunk['document_id'],
                "user_id": chunk['user_id'],
                "content": chunk['content'],
                "chunk_metadata": json.dumps(chunk.get('chunk_metadata', {})),  # Convert to JSON string
                "embedding": embedding
            }
            documents.append(doc)
        
        try:
            self.search_client.upload_documents(documents)
            return True
        except Exception as e:
            print(f"Error indexing documents: {str(e)}")
            return False
    
    
    def similarity_search(self, query: str, user_id: int, filters: Dict = None, k: int = 10):
        #query_embedding = self.embedding_service.create_embeddings([query])[0]
        
        # Always include user_id in filter
        filter_conditions = [f"user_id eq {user_id}"]
        
        # Add additional document filters if provided
        if filters and 'document_id' in filters:
            if isinstance(filters['document_id'], list):
                doc_filter = " or ".join([f"document_id eq {doc_id}" for doc_id in filters['document_id']])
                filter_conditions.append(f"({doc_filter})")
            else:
                filter_conditions.append(f"document_id eq {filters['document_id']}")

        # Combine all filter conditions
        filter_string = " and ".join(filter_conditions)

        try:
            results = self.search_client.search(
                search_text=query,
                #vector=query_embedding,
                #vector_fields="embedding",
                select=["id", "document_id", "user_id", "content", "chunk_metadata"],
                filter=filter_string,
                top=k
            )
            
            return list(results)
        except Exception as e:
            print(f"Error in similarity search: {str(e)}")
            raise