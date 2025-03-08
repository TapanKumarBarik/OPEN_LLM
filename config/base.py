class Config:
    """Base configuration."""
    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'replace-this-with-a-real-secret-key'
    
    # JWT settings
    JWT_SECRET_KEY = 'replace-this-with-a-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # AI Model settings
    AI_MODEL_PATH = 'models'
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
    
    # Azure Storage
    AZURE_STORAGE_CONNECTION_STRING = 'your-connection-string'