
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_migrate import Migrate


# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class):
    """Application factory function"""
    app = Flask(__name__,
                template_folder='templates', 
                static_folder='static')
    app.config.from_object(config_class)
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False  
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    # Register routes
    from app.routes import init_routes
    init_routes(app)

    return app