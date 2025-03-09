from celery import shared_task
from app import db
from app.models import Document, DocumentChunk
from app.services.document_processing.base import DocumentParserFactory
from app.services.embedding.embedding_service import EmbeddingService
import tempfile

@shared_task
def process_document(doc_id: int):
    try:
        document = Document.query.get(doc_id)
        if not document:
            return False
            
        # Update status
        document.status = 'processing'
        db.session.commit()
        
        # Download file from blob storage
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Your blob download logic here
            temp_path = temp_file.name
            
            # Parse document
            metadata = {
                'document_id': doc_id,
                'user_id': document.user_id,
                'filename': document.filename,
                'created_at': document.created_at.isoformat()
            }
            
            parser = DocumentParserFactory.get_parser(document.filename)
            chunks = parser.parse(temp_path, metadata)
            
            # Create embeddings
            embedding_service = EmbeddingService()
            texts = [chunk.content for chunk in chunks]
            embeddings = embedding_service.create_embeddings(texts)
            
            # Save chunks with embeddings
            for chunk, embedding in zip(chunks, embeddings):
                doc_chunk = DocumentChunk(
                    document_id=doc_id,
                    user_id=document.user_id,
                    content=chunk.content,
                    metadata=chunk.metadata
                )
                doc_chunk.set_embedding(embedding)
                db.session.add(doc_chunk)
            
            document.status = 'processed'
            db.session.commit()
            
        return True
        
    except Exception as e:
        document.status = 'failed'
        db.session.commit()
        raise e