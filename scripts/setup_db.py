import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Document, AuditLog  # Import all models
from werkzeug.security import generate_password_hash
from config.development import DevelopmentConfig
from dotenv import load_dotenv

load_dotenv()

def init_db():
    """Initialize database and create admin user"""
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        try:
            # Create all tables
            db.create_all()  # This will create tables for all models
            
            # Check if admin user exists
            admin = User.query.filter_by(username=os.getenv('ADMIN_USERNAME', 'admin')).first()
            if not admin:
                # Create admin user from environment variables
                admin = User(
                    username=os.getenv('ADMIN_USERNAME', 'admin'),
                    email=os.getenv('ADMIN_EMAIL', 'admin@example.com'),
                    password_hash=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
                    role='admin'
                )
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created successfully!")
                print(f"Username: {admin.username}")
                print("Password: [hidden] - check .env file")
            else:
                print("ℹ️ Admin user already exists")

            print("✅ Database initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    init_db()