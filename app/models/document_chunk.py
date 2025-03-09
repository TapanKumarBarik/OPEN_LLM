from app import db
from datetime import datetime
import numpy as np

class DocumentChunk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(db.ARRAY(db.Float), nullable=True)
    chunk_metadata = db.Column(db.JSON, nullable=False)  # Changed from metadata to chunk_metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    document = db.relationship('Document', backref='chunks')
    user = db.relationship('User', backref='document_chunks')

    def set_embedding(self, embedding_array):
        self.embedding = np.array(embedding_array).astype(float).tolist()