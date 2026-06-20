from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_smorest import Api
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
migrate = Migrate()
api = Api()
ma = Marshmallow()
jwt = JWTManager()
