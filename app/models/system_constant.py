# app/models/system_constant.py
from app import db

class SystemConstant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    key = db.Column(db.String(100), nullable=False)
    value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(500))
    is_editable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    __table_args__ = (db.UniqueConstraint('category', 'key'),)