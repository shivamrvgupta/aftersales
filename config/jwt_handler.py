from flask import jsonify
from flask_jwt_extended import JWTManager
from models.user import UserModel, UserRoleAssignmentsModel
from models.roles import UserRoleModel

def jwt_setup(app):
    jwt = JWTManager(app)

    # Add custom claims to the JWT token
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        print(f'Identity: {identity}')
        user = UserModel.query.filter(UserModel.user_id == identity).first()
        if not user:
            return {}

        user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()
        if not user_role:
            return {}

        role = UserRoleModel.query.filter(UserRoleModel.role_id == user_role.role_id).first()
        if not role:
            return {}

        return {'user_id': user.user_id, 'role': role.name}

    # Common error response structure for JWT-related issues
    def jwt_error_response(status_code, message, data=None):
        return jsonify({
            'status': False,
            'status_code': status_code,
            'message': message,
            'data': data or {}
        }), status_code

    # Handle expired token
    @jwt.expired_token_loader
    def my_expired_token_callback(jwt_header, jwt_data):
        response = {
            "user_id": jwt_data.get("user_id"),
            "type": jwt_data.get("type"),
            "role": jwt_data.get("role"),
        }
        return jwt_error_response(401, 'The token has expired', response)

    # Handle invalid token
    @jwt.invalid_token_loader
    def my_invalid_token_callback(error_message):
        return jwt_error_response(401, 'The token is invalid', {'error': error_message})

    # Handle missing token
    @jwt.unauthorized_loader
    def my_unauthorized_callback(error):
        return jwt_error_response(401, 'Authorization token is missing', {'error': str(error)})
