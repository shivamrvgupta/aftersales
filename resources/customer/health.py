from flask_restful import Resource
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt, decode_token
from flask_smorest import Blueprint, abort

blp = Blueprint("Health", "health", description="Operations to check health")

@blp.route("/health")
class Health(Resource):
    @jwt_required()
    def get(self):
        jwt = get_jwt()
        print(f"JWT Claims received: {jwt}")
        if not jwt.get("is_customer"):
           return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
        return {"message": "Success"}, 200
