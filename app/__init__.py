
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from flask_migrate import Migrate

from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt




# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
login_manager = LoginManager()
migrate = Migrate()









def role_required(roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") in roles:
                return fn(*args, **kwargs)
            return jsonify({"error": "Unauthorized access"}), 403
        return decorator
    return wrapper


def create_app(config_class):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config_class)



    # Set up JWT to use cookies (for development, cookie secure is disabled)
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_COOKIE_SECURE'] = False  
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Enable in production!
    app.config['JWT_HEADER_TYPE'] = 'Bearer'

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    login_manager.init_app(app)

    from app.api.auth import auth_bp
    from app.api.admin import admin_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    from app.routes import init_routes
    init_routes(app)

    return app