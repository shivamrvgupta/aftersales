from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas.auth import UserSchema, UserRoleSchema
from marshmallow import ValidationError
from models import roles as roleModel
from flask_jwt_extended import jwt_required, get_jwt , get_jwt_identity
from sqlalchemy.orm import Session
from flask import request, jsonify
from flask_bcrypt import Bcrypt
from db import db
from datetime import datetime

bcrypt = Bcrypt()

blp = Blueprint("Roles", "roles", description="Operations to Add Roles")


@blp.route("/get-roles")
class Roles(MethodView):
    @jwt_required()
    def get(self):
        try : 
            jwt = get_jwt()

            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
            
            roles = roleModel.UserRoleModel.query.all()
            if not roles:
                abort(404, {"status": False, "status_code": 404, "message": "Role not found", "data": {}})

            roleSchema = UserRoleSchema(many=True)
            roles = roleSchema.dump(roles)

            responseData = {
                "roles": roles
            }

            return jsonify({"status": True, "status_code": 200, "message": "Role found", "data": responseData})

        except ValidationError as err:  
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(err)}), 500


@blp.route("/add-roles")
class AddRoles(MethodView):
    @jwt_required()
    def post(self):
        try:
            
            jwt = get_jwt()

            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            # Validate incoming data with userSchema
            schema = UserRoleSchema()
            data = schema.load(request.get_json())
            print(request.get_json())

            # Create New Roles 
            if db.session.query(roleModel.UserRoleModel).filter_by(name=data['name']).first():
                return jsonify({"status" : False, "status_code" : 409,"message": "Role with this name already exists.",  "data" : {} }), 409
            
            # Print the logs

            new_role = roleModel.UserRoleModel(
                name=data['name'],
                description=data['description']
            )

            db.session.add(new_role)
            db.session.commit()

            responseData = {
                "role_id": new_role.role_id,
                "name": new_role.name,
                "description": new_role.description
            }

            return jsonify({"status" : True, "status_code" : 201,"message": "Role Added Successfully.",  "data" : responseData }), 201
        except ValidationError as err:
            return jsonify({"status" : False, "status_code" : 500,"message": "An error occurred", "error": str(err)}), 500

@blp.route("/update-role")
class UpdateRoles(MethodView):
    @jwt_required()
    def put(self):
        try:

            jwt = get_jwt()

            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
            
            # Validate incoming data with userSchema
            schema = UserRoleSchema()
            data = schema.load(request.get_json())

            # Create New Roles
            roles = db.session.query(roleModel.UserRoleModel).filter_by(name=data['name']).first()

            if not roles:
                return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}}), 404
            
            roles.name = data['name'] or roles.name
            roles.description = data['description'] or roles.description

            db.session.commit()

            roleSchema = UserRoleSchema()
            responseData = roleSchema.dump(roles)

            return jsonify({"status": True, "status_code": 200, "message": "Role Updated Successfully", "data": responseData}), 200

        except ValidationError as err:
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(err)}), 500
        
        finally:
            db.session.close()

@blp.route("/delete-role")
class DeleteRoles(MethodView):
    @jwt_required()
    def delete(self):
        try:

            jwt = get_jwt()

            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
            
            # Validate incoming data with userSchema
            data = request.get_json()

            # Create New Roles
            roles = db.session.query(roleModel.UserRoleModel).filter_by(name=data['name']).first()

            responseData = {
                "name": roles.name,
                "description": roles.description
            }
            if not roles:
                return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}}), 404
            
            db.session.delete(roles)
            db.session.commit()

            return jsonify({"status": True, "status_code": 200, "message": "Role Deleted Successfully", "data": {responseData}}), 200
        
        except ValidationError as err:
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(err)}), 500
        
        finally:
            db.session.close()