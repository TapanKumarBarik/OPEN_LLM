from abc import ABC, abstractmethod
from typing import List, Dict
import os
from datetime import datetime

class DocumentChunk:
    def __init__(self, content: str, metadata: Dict):
        self.content = content
        self.metadata = metadata
        self.metadata['chunk_created_at'] = datetime.utcnow().isoformat()

class BaseDocumentParser(ABC):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def parse(self, file_path: str, metadata: Dict) -> List[DocumentChunk]:
        pass

    def _create_chunks(self, text: str, metadata: Dict) -> List[DocumentChunk]:
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > self.chunk_size and current_chunk:
                chunks.append(DocumentChunk(
                    content=' '.join(current_chunk),
                    metadata=metadata.copy()
                ))
                current_chunk = []
                current_size = 0
            current_chunk.append(word)
            current_size += word_size

        if current_chunk:
            chunks.append(DocumentChunk(
                content=' '.join(current_chunk),
                metadata=metadata.copy()
            ))

        return chunks

class DocumentParserFactory:
    _parsers = {}

    @classmethod
    def register_parser(cls, extensions: List[str], parser_class):
        for ext in extensions:
            cls._parsers[ext.lower()] = parser_class

    @classmethod
    def get_parser(cls, file_path: str, chunk_size: int = 500) -> BaseDocumentParser:
        ext = os.path.splitext(file_path)[1].lower()
        parser_class = cls._parsers.get(ext)
        if not parser_class:
            raise ValueError(f"No parser registered for extension {ext}")
        return parser_class(chunk_size=chunk_size)