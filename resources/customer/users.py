from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas.auth import UserProfileSchema , UserAddressSchema, UserSchema, AddressResponseSchema, CompanyResponseSchema
from marshmallow import ValidationError
from models.user import UserModel , UserAddressModel, CompanyModel  
from models.user import UserRoleAssignmentsModel
from models.roles import UserRoleModel

from sqlalchemy.orm import Session
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from db import db
from datetime import datetime

bcrypt = Bcrypt()

blp = Blueprint("Users", "users", description="Operations to check manage users")


@blp.route("/get-profile" , methods=["GET"])
class UserProfile(MethodView):    
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()
            print(f"JWT Claims received: {jwt}")

            if not jwt.get("user_id"):
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401

            user_id = jwt.get("user_id")
            users = UserModel.query.filter(UserModel.user_id == user_id).first()
            
            if not users:
                abort(404, {"status": False, "status_code": 404, "message": "User not found", "data": {}})

            user_role_assignments = UserRoleAssignmentsModel.query.filter_by(user_id=user_id).first()
            if not user_role_assignments:
                abort(404, {"status": False, "status_code": 404, "message": "User Role not found", "data": {}})

            user_role = UserRoleModel.query.filter_by(role_id=user_role_assignments.role_id).first()
            if not user_role:
                abort(404, {"status": False, "status_code": 404, "message": "Role not found", "data": {}})

            userData = UserProfileSchema().dump(users),

            if users.customer_type == "Business":
                company = CompanyModel.query.filter(CompanyModel.user_id == users.user_id).first()
                company_schema = CompanyResponseSchema()
                company_data = company_schema.dump(company)
                response_data = {
                    "user": userData,
                    "company": company_data,
                    "role": user_role.name
                }

                return jsonify({"status": True, "status_code": 200, "message": "User Found Successfully.", "data": response_data}), 200
            else:
                response_data = {
                    "user": userData,
                    "role": user_role.name
                }
                return jsonify({"status": True, "status_code": 200, "message": "User Found Successfully.", "data": response_data}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()

@blp.route("/fetch-user" , methods=["GET"])
class UserProfile(MethodView):    
    @jwt_required()
    def get(self):

        jwt = get_jwt()
        print(f"JWT Claims received: {jwt}")

        if not jwt.get("user_id"):
            return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401

        user_id = jwt.get("user_id")
        users = UserModel.query.filter(UserModel.user_id == user_id).first()
        
        if not users:
            abort(404, {"status": False, "status_code": 404, "message": "User not found", "data": {}})

        user_role_assignments = UserRoleAssignmentsModel.query.filter_by(user_id=user_id).first()
        if not user_role_assignments:
            abort(404, {"status": False, "status_code": 404, "message": "User Role not found", "data": {}})

        user_role = UserRoleModel.query.filter_by(role_id=user_role_assignments.role_id).first()
        if not user_role:
            abort(404, {"status": False, "status_code": 404, "message": "Role not found", "data": {}})

        userAddress = UserAddressModel.query.filter_by(user_id=user_id).first()
        
        if not userAddress:
            userAddress = { "message" : "No address Available"}

        
        userData = UserProfileSchema().dump(users),
        userAddress = UserAddressSchema().dump(userAddress),

        if users.customer_type == "Business":
            company = CompanyModel.query.filter(CompanyModel.user_id == users.user_id).first()
            company_schema = CompanyResponseSchema()
            company_data = company_schema.dump(company)
            response_data = {
                "user": userData,
                "company": company_data,
                "role": user_role.name,
                "address": userAddress
            }

            return jsonify({"status": True, "status_code": 200, "message": "User Found Successfully.", "data": response_data}), 200
        else:
            response_data = {
                "user": userData,
                "role": user_role.name,
                "address": userAddress
            }
            return jsonify({"status": True, "status_code": 200, "message": "User Found Successfully.", "data": response_data}), 200


@blp.route("/update-profile/<int:user_id>", methods=["PUT"])
class UserProfileUpdate(MethodView):
    @jwt_required()
    def put(self, user_id):
        user = UserModel.query.filter_by(user_id=user_id).first()
        
        if not user:
            abort(404, {"status": False, "status_code": 404, "message": "User not found", "data": {}})

        jwt = get_jwt()
        print(f"JWT Claims received: {jwt}")

        if jwt.get("user_id") != user_id:
            return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
        
        try:
            schema = UserProfileSchema()
            user_data = schema.load(request.get_json())

            user.name = user_data.get("name", user.name)
            user.email = user_data.get("email", user.email) or ""
            user.phone_number = user_data.get("phone_number", user.phone_number)
            
            db.session.commit()
            
            updated_user_data = UserProfileSchema().dump(user)
            
            user_role_assignments = UserRoleAssignmentsModel.query.filter_by(user_id=user_id).first()
            if not user_role_assignments:
                abort(404, {"status": False, "status_code": 404, "message": "User Role not found", "data": {}})
            
            user_role = UserRoleModel.query.filter_by(role_id=user_role_assignments.role_id).first()
            if not user_role:
                abort(404, {"status": False, "status_code": 404, "message": "Role not found", "data": {}})

            # check the user Type   
            if user.customer_type == "Business":
                company = CompanyModel.query.filter(CompanyModel.user_id == user.user_id).first()
                company_schema = CompanyResponseSchema()
                company_data = company_schema.dump(company)
                response_data = {
                    "user": updated_user_data,
                    "company": company_data,
                    "role": user_role.name,
                }
                return jsonify({"status": True, "status_code": 200, "message": "User updated successfully.", "data": response_data}), 200
            else:
                response_data = {
                    "user": updated_user_data,
                    "role": user_role.name
                }
                return jsonify({"status": True, "status_code": 200, "message": "User updated successfully.", "data": response_data}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()


@blp.route("/get-address" , methods=["GET"])
class UserAddress(MethodView):    
    @jwt_required()
    def get(self):

        jwt = get_jwt()
        print(f"JWT Claims received: {jwt}")

        if not jwt.get("user_id"):
            return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401

        user_id = jwt.get("user_id")
        users = UserModel.query.filter(UserModel.user_id == user_id).first()
        
        if not users:
            return jsonify({"status": False, "status_code": 404, "message": "User not found", "data": {}})

        userAddress = UserAddressModel.query.filter_by(user_id=user_id).first()
        if not userAddress:
            return jsonify({"status": True, "status_code": 200, "message": "No Address Available", "data": {}})

        user_role_assignments = UserRoleAssignmentsModel.query.filter_by(user_id=user_id).first()
        if not user_role_assignments:
            return jsonify({"status": False, "status_code": 404, "message": "User Role not found", "data": {}})

        user_role = UserRoleModel.query.filter_by(role_id=user_role_assignments.role_id).first()
        if not user_role:
            return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}})

        userData = {
            "userData": AddressResponseSchema().dump(userAddress),
            "role": user_role.name
        }

        return jsonify({"status": True, "status_code": 200, "message": "User's Address found", "data": userData})

@blp.route("/add-address", methods=["POST"])
class UserAddressAdd(MethodView):
    @jwt_required()
    def post(self):
        try :
            jwt = get_jwt()

            if not jwt.get("user_id"):
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
            
            user_id = jwt.get("user_id")

            user = UserModel.query.filter_by(user_id=user_id).first()

            if not user:
                abort(404, {"status": False, "status_code": 404, "message": "User not found", "data": {}})

            schema = UserAddressSchema()
            data = schema.load(request.get_json())
            
            if not data:
                abort(400, {"status": False, "status_code": 400, "message": "Invalid data", "data": {}})

            userAddress = UserAddressModel(user_id = user_id,**data)

            db.session.add(userAddress)
            db.session.commit()

            responseData = {
                "addressData" : AddressResponseSchema().dump(userAddress)
            }

            return {"status": True, "status_code": 200, "message": "User Address added successfully", "data": responseData}, 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()   
        

@blp.route("/update-address/<int:address_id>", methods=["PUT"])
class UserAddressUpdate(MethodView):
    @jwt_required()
    def put(self, address_id):
        jwt = get_jwt()

        if not jwt.get("user_id"):
            return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
        
        user_id = jwt.get("user_id")

        user = UserModel.query.filter_by(user_id=user_id).first()
        
        if not user:
            return jsonify({"status": False, "status_code": 404, "message": "User not found", "data": {}}), 404

        userAddress = UserAddressModel.query.filter_by(user_id=user_id, address_id=address_id).first()
        
        if not userAddress:
            return jsonify({"status": False, "status_code": 404, "message": "User Address not found", "data": {}}), 404

        try:
            schema = UserAddressSchema()
            user_data = schema.load(request.get_json())

            userAddress.address_1 = user_data.get("address", userAddress.address_1)
            userAddress.address_2 = user_data.get("address_2", userAddress.address_2)
            userAddress.city = user_data.get("city", userAddress.city)
            userAddress.state = user_data.get("state", userAddress.state)
            userAddress.country = user_data.get("country", userAddress.country)
            userAddress.pincode = user_data.get("pincode", userAddress.pincode)

            db.session.commit()
            
            updated_user_data = UserAddressSchema().dump(userAddress)
            
            user_role_assignments = UserRoleAssignmentsModel.query.filter_by(user_id=user_id).first()
            if not user_role_assignments:
                return jsonify({"status": False, "status_code": 404, "message": "User Role not found", "data": {}}), 404
            
            user_role = UserRoleModel.query.filter_by(role_id=user_role_assignments.role_id).first()
            if not user_role:
                return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}}), 404

            userData = {
                "addressData": updated_user_data,
                "role": user_role.name
            }
            return jsonify({"status": True, "status_code": 200, "message": "User's Address updated successfully", "data": userData}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()


@blp.route("/delete-address/<int:address_id>", methods=["DELETE"])
class DeleteUserAddress(MethodView):
    @jwt_required()
    def delete(self, address_id):
        jwt = get_jwt()

        if not jwt.get("user_id"):
            return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
        
        user_id = jwt.get("user_id")

        try:
            user = UserModel.query.filter_by(user_id=user_id).first()

            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User not found", "data": {}}), 404

            userAddress = UserAddressModel.query.filter_by(user_id=user_id, address_id=address_id).first()

            if not userAddress:
                return jsonify({"status": False, "status_code": 404, "message": "User Address not found", "data": {}}), 404

            db.session.delete(userAddress)
            db.session.commit()

            return jsonify({"status": True, "status_code": 200, "message": "User's Address deleted successfully", "data": {}}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()
