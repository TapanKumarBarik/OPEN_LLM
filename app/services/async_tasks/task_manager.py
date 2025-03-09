from threading import Thread, Lock
from typing import Callable
from flask import current_app
from app import db
from app.models import Document, DocumentChunk
from app.services.document_processing.base import DocumentParserFactory
from app.services.embedding.embedding_service import EmbeddingService
from azure.storage.blob import BlobServiceClient
import os
import tempfile


# Singleton pattern for embedding service
class EmbeddingServiceSingleton:
    _instance = None
    _lock = Lock()
    
    @classmethod
    def get_instance(cls) -> EmbeddingService:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("Initializing EmbeddingService - Loading model...")
                    cls._instance = EmbeddingService()
        return cls._instance

class BackgroundTaskManager:
    @staticmethod
    def run_task(func: Callable, *args, **kwargs):
        app = current_app._get_current_object()
        
        def run_with_context(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)
        
        thread = Thread(target=run_with_context, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

def train_document_background(doc_id: int):
    try:
        print("#################################################")
        print(f"Training started for document ID: {doc_id}")
        print("#################################################")

        # Fetch document from DB
        temp_file = None
        document = Document.query.get(doc_id)
        if not document:
            return False
            
        # Get document from blob storage
        container_name = f"user-{document.user_id}"
        blob_service_client = BlobServiceClient.from_connection_string(current_app.config['AZURE_STORAGE_CONNECTION_STRING'])
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(document.blob_path)
        
        # Download to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.filename)[1]) as temp_file:
            blob_data = blob_client.download_blob()
            temp_file.write(blob_data.readall())
            temp_file.flush()
            
            # Create metadata
            metadata = {
                'document_id': doc_id,
                'user_id': document.user_id,
                'filename': document.filename,
                'created_at': document.created_at.isoformat()
            }

        # 1. Get appropriate parser based on file extension
        parser = DocumentParserFactory.get_parser(document.filename)
        if not parser:
            raise Exception(f"No parser found for file type: {document.filename}")
        
        print("#################################################")
        print(f"Parser found: {parser}")
        print("#################################################")

        # Update status to processing
        document.status = 'processing'
        db.session.commit()
        print(f"Document {doc_id} status updated to 'processing'.")

        # 2. Parse document into chunks
        try:
            metadata = {
                'document_id': doc_id,
                'user_id': document.user_id,
                'filename': document.filename,
                'created_at': document.created_at.isoformat()
            }
            print(f"Metadata for document {doc_id}: {metadata}")

            chunks = parser.parse(temp_file.name, metadata) 
            
            print(f"Document {doc_id} parsed into {len(chunks)} chunks.")

            if not chunks:
                raise Exception("No text content extracted from document")
                
            # Update status to chunking
            document.status = 'chunking'
            db.session.commit()
            print(f"Document {doc_id} status updated to 'chunking'.")

            # 3. Create embeddings using singleton instance
            embedding_service = EmbeddingServiceSingleton.get_instance()
            texts = [chunk.content for chunk in chunks]

            print(f"Generating embeddings for {len(texts)} chunks...")

            # Update status to embedding
            document.status = 'embedding'
            db.session.commit()
            print(f"Document {doc_id} status updated to 'embedding'.")

            embeddings = embedding_service.create_embeddings(texts)
            print(f"Embeddings created for {len(embeddings)} chunks.")

            # 4. Store chunks with embeddings
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                print(f"Storing chunk {idx+1}/{len(chunks)} for document {doc_id}")
                doc_chunk = DocumentChunk(
                    document_id=doc_id,
                    user_id=document.user_id,
                    content=chunk.content,
                    chunk_metadata=chunk.metadata  # Note: using chunk_metadata instead of metadata
                )
                doc_chunk.set_embedding(embedding)
                db.session.add(doc_chunk)

            db.session.commit()
            print(f"All chunks for document {doc_id} stored successfully.")

            # 5. Update document status
            document.status = 'trained'
            db.session.commit()
            print(f"Document {doc_id} successfully trained.")
            return True
            
        except Exception as e:
            print(f"Training failed for document {doc_id} during parsing/embedding: {str(e)}")  # Add logging
            document = Document.query.get(doc_id)
            if document:
                document.status = 'training_failed'
                document.error_message = str(e)
                db.session.commit()
            return False
        
    except Exception as e:
        print(f"Training failed for document {doc_id} due to unexpected error: {str(e)}")  # Add logging
        document = Document.query.get(doc_id)
        if document:
            document.status = 'training_failed'
            document.error_message = str(e)
            db.session.commit()
        return False
    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
