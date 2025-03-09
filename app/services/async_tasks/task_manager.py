from threading import Thread
from typing import Callable
from flask import current_app
from app import db
from app.models import Document

class BackgroundTaskManager:
    @staticmethod
    def run_task(func: Callable, *args, **kwargs):
        app = current_app._get_current_object()  # Get the actual app object
        
        def run_with_context(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)
        
        thread = Thread(target=run_with_context, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

def train_document_background(doc_id: int):
    try:
        document = Document.query.get(doc_id)
        if not document:
            return False
            
        # Add your document training logic here
        # For example:
        # 1. Process document
        # 2. Create embeddings
        # 3. Store in vector database
        
        document.status = 'trained'
        db.session.commit()
        return True
        
    except Exception as e:
        document = Document.query.get(doc_id)
        if document:
            document.status = 'training_failed'
            db.session.commit()
        return False