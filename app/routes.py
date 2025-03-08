

from flask import render_template, redirect, url_for, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import User

def init_routes(app):
    @app.route('/')
    def home():
        return render_template('index.html')

    
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