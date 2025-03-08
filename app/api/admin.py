# app/api/admin.py

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app.models.system_constant import SystemConstant
from app import db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/settings/constants', methods=['GET'])
@jwt_required()
def get_constants():
    constants = SystemConstant.query.all()
    return jsonify([{
        'id': c.id,
        'category': c.category,
        'key': c.key,
        'value': c.value,
        'description': c.description,
        'is_editable': c.is_editable
    } for c in constants])

@admin_bp.route('/settings/constants/by-key', methods=['PUT'])
@jwt_required()
def update_constant_by_key():
    data = request.get_json()
    constant = SystemConstant.query.filter_by(
        category=data['category'],
        key=data['key']
    ).first_or_404()
    
    if not constant.is_editable:
        return jsonify({'error': 'This constant cannot be modified'}), 403
        
    constant.value = data['value']
    db.session.commit()
    
    return jsonify({
        'id': constant.id,
        'category': constant.category,
        'key': constant.key,
        'value': constant.value,
        'description': constant.description,
        'is_editable': constant.is_editable
    })