from flask_restful import Resource
from flask.views import MethodView
from flask import render_template, redirect, session
from flask_smorest import Blueprint, abort
from schemas.auth import UserSchema, UserResponseSchema , UserRoleSchema
from models import UserModel , UserRoleModel , UserRoleAssignmentsModel, EmailVerification , CompanyModel
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt , get_jwt_identity
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from db import db

import secrets
bcrypt = Bcrypt()

blp = Blueprint("AdminUser", "adminUser", description="Operations to do Watchout all users in the DB")

@blp.route("/customer-lists")
class CustomerList(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()

            if not jwt: 
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
            
            if jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                user_id = jwt.get("user_id")
                user = UserModel.query.get(user_id)
                users = UserModel.query.all()

                schema = UserResponseSchema()
                loggedUser = {
                    "user": schema.dump(user),
                    "role": jwt.get("role")
                }
                
                # Check the users Type is Customer 
                customer_list = []

                for user in users:
                    user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()

                    if user_role:
                        role = UserRoleModel.query.filter(UserRoleModel.role_id == user_role.role_id).first()
                        if role:
                            if role.name == 'Customer':
                                customer_list.append(user)

                customerSchema = UserSchema(many=True)
                responseData = customerSchema.dump(customer_list)

                count = len(responseData)

                userData = {
                    "loggedUser": loggedUser,  # Use a string key here
                    "users": responseData, 
                    "count": count
                }
                return jsonify({"status": True, "status_code": 200, "message": "User's Address updated successfully", "data": userData}), 200

            else:
                return jsonify({"status": True, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500


@blp.route("/customer-list")
class CustomerList(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()

            if not jwt: 
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
            
            if jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                user_id = jwt.get("user_id")
                user = UserModel.query.get(user_id)
                users = UserModel.query.all()

                schema = UserResponseSchema()
                loggedUser = {
                    "user": schema.dump(user),
                    "role": jwt.get("role")
                }
                
                # Check the users Type is Customer 
                customer_list = []

                for user in users:
                    user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()

                    if user_role:
                        role = UserRoleModel.query.filter(UserRoleModel.role_id == user_role.role_id).first()
                        if role:
                            if role.name == 'Customer':
                                customer_list.append(user)

                customerSchema = UserSchema(many=True)
                responseData = customerSchema.dump(customer_list)

                count = len(responseData)

                userData = {
                    "users": responseData, 
                    "count": count
                }
                return jsonify({"status": True, "status_code": 200, "message": "User's Address updated successfully", "data": userData}), 200

            else:
                return jsonify({"status": True, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500


@blp.route("/others-lists")
class OthersList(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()

            # Check if the JWT is valid and contains the required role information
            if not jwt:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
            
            # Ensure the user has the appropriate role
            if jwt.get("role") in ["SuperAdmin", "Admin"]:
                user_id = jwt.get("user_id")
                user = UserModel.query.get(user_id)
                users = UserModel.query.all()

                schema = UserResponseSchema()
                logged_user = {
                    "user": schema.dump(user),
                    "role": jwt.get("role")
                }

                # Retrieve users whose type is not 'Customer'
                other_lists = []

                for user in users:
                    user_role = UserRoleAssignmentsModel.query.filter(
                        UserRoleAssignmentsModel.user_id == user.user_id
                    ).first()

                    if user_role:
                        role = UserRoleModel.query.filter(
                            UserRoleModel.role_id == user_role.role_id
                        ).first()
                        if role and role.name != 'Customer':
                            other_lists.append(user)

                # Serialize the response data
                customer_schema = UserSchema(many=True)
                response_data = customer_schema.dump(other_lists)
                count = len(response_data)

                # Prepare the user data for the response
                user_data = {
                    "users": response_data,
                    "count": count
                }

                return jsonify({
                    "status": True,
                    "status_code": 200,
                    "message": "Other users' data retrieved successfully",
                    "data": user_data
                }), 200

            # If the role is not authorized, return 401
            return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({
                "status": False,
                "status_code": 500,
                "message": "An error occurred",
                "error": str(e)
            }), 500
   

