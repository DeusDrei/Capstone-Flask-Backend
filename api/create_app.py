from flask import Flask, request, jsonify
from flask_cors import CORS
from .middleware import jwt_required
from .config import Config
from .extensions import db, migrate, api, ma, jwt
from .routes import auth_blueprint, user_blueprint

from .seeds.users import register_commands as register_users

def create_app():
    app = Flask(__name__)
    # Enable CORS for all domains on all routes (not recommended for production)
    CORS(app)

    # Or enable CORS for specific domains only (recommended for production)
    # CORS(app, resources={r"/*": {"origins": ["https://flutter-frontend.example.com", "https://angular-frontend.example.com"]}})
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)
    api.init_app(app)

    # @app.before_request
    # def check_authentication():
    #     unprotected_endpoints = ["/auth/login"]
    #     if request.path not in unprotected_endpoints: 
    #         jwt_required(request)
        
        
    register_users(app)
    
    api.register_blueprint(auth_blueprint)
    api.register_blueprint(user_blueprint)

    
    return app
