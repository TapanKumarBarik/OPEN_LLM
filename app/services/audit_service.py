# app/services/audit_service.py
from app import db
from app.models.audit_log import AuditLog

def log_activity(user_id, action, details=None):
    """
    Log user activity
    Args:
        user_id: ID of the user performing the action
        action: Description of the action (e.g., 'login', 'logout', 'view_page')
        details: Additional details about the action
    """
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            details=details
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {str(e)}")