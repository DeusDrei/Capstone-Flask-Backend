from flask import request, jsonify
from api.services.auth_service import AuthService
from datetime import datetime, UTC
from marshmallow import ValidationError
from api.config import Config

def jwt_required(f):
    """
    A decorator to require JWT verification for specific routes.
    """
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            token = token.split(" ")[1]
            payload = AuthService.decode_access_token(token)
            if payload is None:
                return jsonify({'error': 'Invalid or expired token'}), 401

            request.user_identity = payload['sub']
            return f(*args, **kwargs)
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return wrapper

def log_request():
    """
    A middleware to log request contexts for each endpoint to a NoSQL database.
    """
    try:
        timestamp = datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')

        if (method := request.method) == "GET":
            return
        
        endpoint = request.endpoint

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split("Bearer ")[1] if "Bearer" in auth_header else None
        username = None

        if token:
            payload = AuthService.decode_access_token(token)
            if payload:
                username = payload.get("identity")

        raw_payload = request.get_json(silent=True) or {}
        sanitized_payload = redact_pii(raw_payload)

        log_entry = {
            'timestamp': timestamp,
            'method': method,
            'endpoint': endpoint,
            'ip_address': request.remote_addr,
            'query_params': request.args.to_dict(),
            'path_params': request.view_args or {},
            'payload': sanitized_payload or {},
            'username': username
        }

    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
################################################################
#                    HELPER FUNCTIONS                          #
################################################################
def redact_pii(data):
    """
    Recursively removes PII from request data.
    """
    if isinstance(data, dict):
        return {
            key: "***REDACTED***" if key in Config.SENSITIVE_FIELDS else redact_pii(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [redact_pii(item) for item in data]
    return data
