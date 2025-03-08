from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, set_access_cookies,unset_jwt_cookies
)
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
from datetime import timedelta
from app.models.user import User
from app import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
        
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        # Create access token with role in additional claims
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': user.role},
            expires_delta=timedelta(hours=1)
        )
        response = jsonify({
            'message': 'Logged in successfully',
            'access_token': access_token,
            'user': user.to_dict()
        })
        # Set JWT as cookie in the response
        set_access_cookies(response, access_token)
        return response
    
    return jsonify({'error': 'Invalid username or password'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(response)
    return response

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())



@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing {field}'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Validate role
    allowed_roles = ['user', 'analyst', 'engineer']
    if data['role'] not in allowed_roles:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        
        # Create access token with role claim
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': user.role},
            expires_delta=timedelta(hours=1)
        )
        response = jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        })
        # Set JWT cookie so browser sends it automatically
        set_access_cookies(response, access_token)
        return response, 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing {field}'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Validate role
    allowed_roles = ['user', 'analyst', 'engineer']
    if data['role'] not in allowed_roles:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role=data['role']
        )
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User created successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    
    

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
        
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user details (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
        
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Don't allow changing username
    if data.get('email'):
        user.email = data['email']
    if data.get('role'):
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
        
    try:
        db.session.commit()
        return jsonify({'message': 'User updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Delete user (admin only)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
        
    if current_user_id == user_id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
        
    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500