from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.auth_service import AuthService
from api.schemas.users import UserSchema, UserLoginSchema
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

auth_blueprint = Blueprint('auth', __name__, url_prefix="/auth")

@auth_blueprint.route('/register', methods=['POST'])
def register():
    try:
        data = UserSchema().load(request.json)
        user = AuthService.register_user(data)
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user.id
        }), 201
    except ValidationError as e:
        return jsonify({'error': str(e.messages)}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IntegrityError:
        return jsonify({'error': 'Email or faculty ID already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@auth_blueprint.route('/login', methods=['POST'])
def login():
    login_schema = UserLoginSchema()
    try:
        data = login_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    user = AuthService.authenticate_user(data['email'], data['password'])

    print(user)

    if user is None:
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token = AuthService.create_access_token(identity=user)

    return jsonify({'access_token': access_token}), 200
