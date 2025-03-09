

from flask import render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User
from app.services.audit_service import log_activity
from app.models import User, AuditLog
from app.models.system_constant import SystemConstant
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
from flask_login import login_required, current_user
import os
from datetime import datetime
from app.services.async_tasks.task_manager import BackgroundTaskManager, train_document_background

from app.models.document import Document
from flask import Response  # Add this import
from app.models import DocumentChunk 

from app.services.document_processing.base import DocumentParserFactory
from app.services.document_processing.pdf_parser import PdfParser
from app.services.document_processing.docx_parser import DocxParser
from app.services.document_processing.ppt_parser import PptParser
import tempfile

def init_routes(app):
    
    
    # Register parsers
    DocumentParserFactory.register_parser(['.pdf'], PdfParser)
    DocumentParserFactory.register_parser(['.docx', '.doc'], DocxParser)
    DocumentParserFactory.register_parser(['.pptx', '.ppt'], PptParser)
    
    @app.route('/')
    def home():
        return render_template('index.html')
    
    
    @app.context_processor
    def inject_site_settings():
        try:
            site_name = SystemConstant.query.filter_by(
                category='SITE_SETTINGS', 
                key='SITE_NAME'
            ).first().value
            site_footer = SystemConstant.query.filter_by(
                category='SITE_SETTINGS', 
                key='SITE_FOOTER'
            ).first().value
            return {'site_name': site_name, 'site_footer': site_footer}
        except:
            return {'site_name': 'Default Site Name', 'site_footer': 'Default Footer'}
        
    @app.route('/dashboard')
    @jwt_required()
    def dashboard():
        try:
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return redirect(url_for('login'))
                
            user = User.query.get_or_404(current_user_id)
            
            # Add role-based access check
            if user.role not in ['admin', 'analyst', 'engineer', 'user']:
                return jsonify({'error': 'Unauthorized access'}), 403
            
            log_activity(current_user_id, 'view_dashboard')
            return render_template('dashboard/main.html', user=user)
        except Exception as e:
            return redirect(url_for('login'))
    

    @app.route('/login')
    def login():
        # Redirect to dashboard if already logged in
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            return redirect(url_for('dashboard'))
        return render_template('auth/login.html')

    @app.route('/signup')
    def signup():
        return render_template('auth/signup.html')

    @app.route('/profile')
    @jwt_required()
    def profile():
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        return render_template('auth/profile.html', user=user)

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.route('/admin/users')
    @jwt_required()
    def admin_users():
        """Admin user management page"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        if user.role != 'admin':
            return redirect(url_for('dashboard'))
            
        return render_template('admin/users.html')
    
    
    @app.route('/admin/settings')
    @jwt_required()
    def admin_settings_site():
        """Admin settings page"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        if user.role != 'admin':
            return redirect(url_for('dashboard'))
            
        return render_template('admin/settings/site.html', active_tab='site')
    
    @app.route('/admin/settings/constants')
    @jwt_required()
    def admin_settings_constants():
        """Admin constants page"""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        if user.role != 'admin':
            return redirect(url_for('dashboard'))
            
        return render_template('admin/settings/constants.html', active_tab='constants')
    
    
    @app.route('/admin/audit-logs')
    @jwt_required()
    def admin_audit_logs():
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        if user.role != 'admin':
            return redirect(url_for('dashboard'))
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        # Base query with user join
        query = AuditLog.query.join(User)
        
        # Apply search if provided
        if search:
            query = query.filter(
                db.or_(
                    User.username.ilike(f'%{search}%'),
                    AuditLog.action.ilike(f'%{search}%'),
                    AuditLog.details.ilike(f'%{search}%')
                )
            )
        
        # Order and paginate
        logs = query.order_by(AuditLog.timestamp.desc()).paginate(
            page=page, 
            per_page=per_page,
            error_out=False
        )
        
        return render_template(
            'admin/audit_logs.html',
            logs=logs,
            search=search
        )
        
        
    @app.route('/documents')
    @jwt_required()  
    def documents():
        return render_template('documents/index.html')

    @app.route('/api/documents', methods=['POST'])
    @jwt_required()
    def upload_document():
        # 1. First check if file exists in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        
        # 2. Then check if filename is empty
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        # 3. Now we can safely get the filename
        filename = secure_filename(file.filename)
        
        # 4. Check file extension
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in ['.pdf', '.doc', '.docx', '.ppt', '.pptx']:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        current_user_id = get_jwt_identity()
        
        # 5. Check for duplicate filenames
        existing_document = Document.query.filter_by(
            user_id=current_user_id,
            filename=filename
        ).first()
        
        if existing_document:
            return jsonify({
                'error': 'A document with this name already exists. Please rename the file or delete the existing one.'
            }), 400

        
        # Continue with upload if file doesn't exist
        file_extension = os.path.splitext(filename)[1].lower()
        unique_filename = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        # Upload to Azure Blob Storage
        container_name = f"user-{current_user_id}"
        blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
        
        try:
            container_client = blob_service_client.get_container_client(container_name)
            container_client.create_container()
        except:
            container_client = blob_service_client.get_container_client(container_name)
        
        blob_client = container_client.get_blob_client(unique_filename)
        blob_client.upload_blob(file)
        
        # Save document metadata to database
        document = Document(
            filename=filename,
            blob_path=unique_filename,
            user_id=current_user_id,
            status='uploaded',
            created_at=datetime.utcnow()
        )
        db.session.add(document)
        db.session.commit()
        
        return jsonify({'message': 'Document uploaded successfully'})

        
    @app.route('/api/documents/<int:doc_id>', methods=['DELETE'])
    @jwt_required()
    def delete_document(doc_id):
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        document = Document.query.get_or_404(doc_id)
        
        # Check if user owns document or is admin
        if document.user_id != current_user_id and user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
            
        try:
            # Delete from Azure Blob Storage
            container_name = f"user-{document.user_id}"
            blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(document.blob_path)
            blob_client.delete_blob()
            
            # Delete from database
            db.session.delete(document)
            db.session.commit()
            
            return jsonify({'message': 'Document deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
        
        
    @app.route('/api/documents', methods=['GET'])
    @jwt_required()
    def get_documents():
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '')
        
        # Use join to get user information
        query = Document.query.join(User)
        
        # Filter by user_id for non-admin users
        if user.role != 'admin':
            # Change this line to filter on Document model
            query = query.filter(Document.user_id == current_user_id)
        
        if search:
            query = query.filter(Document.filename.ilike(f'%{search}%'))
        
        pagination = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page
        )
        
        return jsonify({
            'documents': [{
                'blob_path': doc.blob_path,
                'id': doc.id,
                'filename': doc.filename,
                'status': doc.status,
                'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': doc.user_id,
                'username': doc.user.username,
                'is_admin': user.role == 'admin'
            } for doc in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        })
        
            
    @app.route('/api/documents/preview/<path:blob_path>')
    @jwt_required()
    def preview_document(blob_path):
        try:
            current_user_id = get_jwt_identity()
            container_name = f"user-{current_user_id}"
            blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            
            blob_data = blob_client.download_blob()
            return Response(
                blob_data.readall(),
                mimetype='application/pdf',
                headers={"Content-Disposition": "inline"}
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500



    @app.route('/api/documents/admin-preview/<int:user_id>/<path:blob_path>')
    @jwt_required()
    def admin_preview_document(user_id, blob_path):
        try:
            current_user_id = get_jwt_identity()
            current_user = User.query.get_or_404(current_user_id)
            
            # Verify admin role
            if current_user.role != 'admin':
                return jsonify({'error': 'Unauthorized access'}), 403
                
            container_name = f"user-{user_id}"
            blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            
            blob_data = blob_client.download_blob()
            return Response(
                blob_data.readall(),
                mimetype='application/pdf',
                headers={"Content-Disposition": "inline"}
            )
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/documents/<int:doc_id>/train', methods=['POST']) 
    @jwt_required()
    def train_document(doc_id):
        try:
            # Get the document first
            document = Document.query.get_or_404(doc_id)
            
            # Verify user has permission
            current_user_id = get_jwt_identity()
            if document.user_id != current_user_id:
                return jsonify({'error': 'Unauthorized'}), 403

            # Start processing
            document.status = 'processing'
            db.session.commit()
            
            # Background task
            BackgroundTaskManager.run_task(train_document_background, doc_id)
            
            return jsonify({'message': 'Processing started'})
            
        except Exception as e:
            # Get document again in case the error occurred before document was fetched
            document = Document.query.get(doc_id)
            if document:
                document.status = 'failed'
                document.error_message = str(e)
                db.session.commit()
            return jsonify({'error': str(e)}), 500
            
            
    
    @app.route('/api/documents/<int:doc_id>/status')
    @jwt_required()
    def get_document_status(doc_id):
        document = Document.query.get_or_404(doc_id)
        return jsonify({
            'status': document.status,
            'progress': document.processing_progress
        })         

   
    @app.route('/dashboard/user/<int:user_id>')
    @jwt_required()
    def view_user_profile(user_id):
        """View user profile (admin only)"""
        current_user_id = get_jwt_identity()
        current_user = User.query.get_or_404(current_user_id)
        
        # Check if admin
        if current_user.role != 'admin':
            return redirect(url_for('dashboard'))
            
        # Get user to view
        user = User.query.get_or_404(user_id)
        log_activity(current_user_id, 'view_user_profile', f'Viewed profile of user {user_id}')
        return render_template('auth/profile.html', user=user)
    
    @app.route('/api/documents/<int:doc_id>/parse', methods=['POST'])
    @jwt_required()
    def parse_document(doc_id):
        temp_file = None
        try:
            current_user_id = get_jwt_identity()
            document = Document.query.get_or_404(doc_id)
            
            # Check permission
            if document.user_id != current_user_id:
                return jsonify({'error': 'Unauthorized'}), 403
    
            # Update document status
            document.status = 'processing'
            db.session.commit()
    
            # Create parser first
            parser = DocumentParserFactory.get_parser(document.filename, chunk_size=app.config.get('CHUNK_SIZE', 500))
            
            # Get document from blob storage and process it
            container_name = f"user-{current_user_id}"
            blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
            container_client = blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(document.blob_path)
            
            # Download and process in the same with block
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(document.filename)[1]) as temp_file:
                # Download blob
                blob_data = blob_client.download_blob()
                temp_file.write(blob_data.readall())
                temp_file.flush()
                
                # Important: Get the temp file path
                temp_path = temp_file.name
                
                # Parse document using the temp file path
                metadata = {
                    'document_id': doc_id,
                    'user_id': current_user_id,
                    'filename': document.filename,
                    'blob_path': document.blob_path,
                    'created_at': document.created_at.isoformat()
                }
                
                # Parse while file is still open
                chunks = parser.parse(temp_path, metadata)
                
                # Store chunks in database
                for chunk in chunks:
                    document_chunk = DocumentChunk(
                        document_id=doc_id,
                        user_id=current_user_id,
                        content=chunk.content,
                        metadata=chunk.metadata
                    )
                    db.session.add(document_chunk)
                
                # Update document status
                document.status = 'processed'
                db.session.commit()
                
                return jsonify({
                    'message': f'Document parsed successfully into {len(chunks)} chunks',
                    'chunk_count': len(chunks)
                })
    
        except Exception as e:
            db.session.rollback()
            if document:
                document.status = 'failed'
                document.error_message = str(e)
                db.session.commit()
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
                
                
    @app.route('/documents/chat')
    @jwt_required()
    def document_chat():
        return render_template('documents/chat.html')

    @app.route('/api/chat/model-info')
    @jwt_required()
    def get_model_info():
        llm = get_llm_instance()
        return jsonify({
            'model_name': llm.get_model_name()
        })