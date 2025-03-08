import os
from dotenv import load_dotenv
from .base import Config
from urllib.parse import quote_plus  # Add this import

# Load environment variables
load_dotenv()

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
    # PostgreSQL database URL from environment variables with URL-encoded password
    SQLALCHEMY_DATABASE_URI = 'postgresql://{user}:{password}@{host}:{port}/{db}'.format(
        user=os.getenv('DB_USER', 'postgres'),
        password=quote_plus(os.getenv('DB_PASSWORD', 'postgres')),  # URL encode the password
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        db=os.getenv('DB_NAME', 'open_llm_db')
    )
    
    # Enable query recording
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Show SQLAlchemy queries
    SQLALCHEMY_ECHO = True