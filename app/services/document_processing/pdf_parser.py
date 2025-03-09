from PyPDF2 import PdfReader
from .base import BaseDocumentParser, DocumentChunk
from typing import List, Dict

class PdfParser(BaseDocumentParser):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
    def parse(self, file_path: str, metadata: Dict) -> List[DocumentChunk]:
        chunks = []
        
        try:
            pdf_reader = PdfReader(file_path)
            total_pages = len(pdf_reader.pages)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                text = page.extract_text()
                
                if not text or not text.strip():
                    # Skip pages without text
                    continue
                
                page_metadata = metadata.copy()
                page_metadata.update({
                    'page_number': page_num,
                    'total_pages': total_pages,
                    'extraction_method': 'text'
                })
                
                page_chunks = self._create_chunks(text, page_metadata)
                chunks.extend(page_chunks)
                    
            return chunks
            
        except Exception as e:
            print(f"Error parsing PDF {file_path}: {str(e)}")
            return []  # Return empty list instead of raising an error