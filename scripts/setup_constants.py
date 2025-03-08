import sys
import os
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.system_constant import SystemConstant
from config.development import DevelopmentConfig

def setup_constants():
    # Load environment variables
    load_dotenv()
    
    # Create app context
    app = create_app(DevelopmentConfig)
    
    with app.app_context():
        try:
            # Create tables first
            print("Creating database tables...")
            db.create_all()
            
            constants = [
                # User roles
                {
                    'category': 'USER_ROLES',
                    'key': 'ROLE_ADMIN',
                    'value': 'admin',
                    'description': 'Administrator role',
                    'is_editable': False
                },
                {
                    'category': 'USER_ROLES', 
                    'key': 'ROLE_ANALYST',
                    'value': 'analyst',
                    'description': 'Business Analyst role',
                    'is_editable': True
                },
                {
                    'category': 'USER_ROLES',
                    'key': 'ROLE_ENGINEER',
                    'value': 'engineer', 
                    'description': 'Data Engineer role',
                    'is_editable': True
                },
                {
                    'category': 'USER_ROLES',
                    'key': 'ROLE_USER',
                    'value': 'user',
                    'description': 'Standard user role',
                    'is_editable': True
                },
                
                {
                'category': 'SITE_SETTINGS',
                'key': 'SITE_NAME',
                'value': 'Open LLM Business Intelligence',
                'description': 'Website name displayed in header and title',
                'is_editable': True
                },
                {
                'category': 'SITE_SETTINGS',
                'key': 'SITE_FOOTER',
                'value': '© 2025 Open LLM Business Intelligence. All rights reserved.',
                'description': 'Footer text',
                'is_editable': True
                }
            ]
            
            # Add system constants
            print("Initializing system constants...")
            for constant in constants:
                if not SystemConstant.query.filter_by(
                    category=constant['category'], 
                    key=constant['key']
                ).first():
                    db.session.add(SystemConstant(**constant))
            
            db.session.commit()
            print("✅ System constants initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == '__main__':
    setup_constants()