from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.document import Document
from app.models.chat_history import ChatHistory
from app.services.vector_store import VectorStore
from app.services.ai.llm_factory import get_llm_instance
from app.services.ai.llm_factory import get_llm_instance

from app import db



chat_bp = Blueprint('chat', __name__)





@chat_bp.route('/model', methods=['GET'])
@jwt_required()
def get_model_info():
    llm = get_llm_instance()
    return jsonify({
        'model_name': llm.get_model_name()
    })

@chat_bp.route('/docs', methods=['POST'])
@jwt_required()
def chat_with_docs():
    
    print("#############################################")
    print("chat_with_docs")
    print("#############################################")
    
    current_user_id = get_jwt_identity()
    
    # Get query from request
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
        
    # Get all user's documents by default
    docs = Document.query.filter_by(user_id=current_user_id).all()
    doc_ids = [doc.id for doc in docs]
    
    if not doc_ids:
        return jsonify({'error': 'No documents found'}), 404
    
    # Get relevant chunks from vector store
    vector_store = VectorStore()
    chunks = vector_store.similarity_search(
        query=query,
        filters={'document_id': {'$in': doc_ids}},
        k=10
    )
    
    # Prepare context and citations
    context = [chunk.content for chunk in chunks]
    citations = [{
        'content': chunk.content,
        'metadata': {
            **chunk.metadata,
            'filename': docs[chunk.metadata['document_id']].filename
        }
    } for chunk in chunks]
    
    # Get configured LLM
    llm = get_llm_instance()
    
    # Generate response
    response = llm.generate_response(
        query=query,
        context=context,
        citations=citations
    )
    
    # Save chat history
    chat = ChatHistory(
        user_id=current_user_id,
        query=query,
        response=response['answer'],
        model_used=llm.get_model_name()
    )
    db.session.add(chat)
    db.session.commit()
    
    return jsonify(response)