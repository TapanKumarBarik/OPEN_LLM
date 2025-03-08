

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

from app.models.document import Document

def init_routes(app):
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
        current_user_id = get_jwt_identity()
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        filename = secure_filename(file.filename)

        # Check if user has already uploaded a file with the same name
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

    @app.route('/api/documents', methods=['GET'])
    @jwt_required()
    def get_documents():
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)  # Get the user from database
        page = request.args.get('page', 1, type=int)
        per_page = 10
        search = request.args.get('search', '')
        
        query = Document.query
        
        # Check role using the user object from database
        if user.role != 'admin':
            query = query.filter_by(user_id=current_user_id)
            
        if search:
            query = query.filter(Document.filename.ilike(f'%{search}%'))
            
        pagination = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page
        )
        
        return jsonify({
            'documents': [{
                'id': doc.id,
                'filename': doc.filename,
                'status': doc.status,
                'created_at': doc.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': doc.user_id
            } for doc in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        })