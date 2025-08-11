from flask import Flask, request, jsonify
from flask_cors import CORS
from .config import Config
from .extensions import db, migrate, api, ma, jwt
from .routes import auth_blueprint, user_blueprint, department_blueprint, college_blueprint, subject_blueprint, universityim_blueprint, serviceim_blueprint, collegeincluded_blueprint

from .seeds.users import register_commands as register_users
from .seeds.departments import register_commands as register_departments
from .seeds.colleges import register_commands as register_colleges
from .seeds.subjects import register_commands as register_subjects
from .seeds.universityims import register_commands as register_universityims
from .seeds.serviceims import register_commands as register_serviceims
from .seeds.collegesincluded import register_commands as register_collegesincluded

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
        
    register_users(app)
    register_departments(app)
    register_colleges(app)
    register_subjects(app)
    register_universityims(app)
    register_serviceims(app)
    register_collegesincluded(app)
    
    api.register_blueprint(auth_blueprint)
    api.register_blueprint(user_blueprint)
    api.register_blueprint(department_blueprint)
    api.register_blueprint(college_blueprint)
    api.register_blueprint(subject_blueprint)
    api.register_blueprint(universityim_blueprint)
    api.register_blueprint(serviceim_blueprint)
    api.register_blueprint(collegeincluded_blueprint)
    
    return app
