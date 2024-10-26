from flask_restful import Resource
from flask.views import MethodView
from flask import render_template, redirect, session , url_for
from flask_smorest import Blueprint, abort
from schemas.auth import UserSchema, UserResponseSchema , LoginEmailSchema, CompanyResponseSchema , RoleSchema
from models import UserModel , UserRoleModel , UserRoleAssignmentsModel, EmailVerification , CompanyModel
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt , get_jwt_identity
from flask_bcrypt import Bcrypt
from db import db
import logging

# Configure logging
from flask_jwt_extended import create_access_token

import secrets
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bcrypt = Bcrypt()

blp = Blueprint("AdminAuth", "adminAuth", description="Operations to do authentication and authorization")

@blp.route("/login")
class Login(MethodView):
    def post(self):
        try:
            print(f"Raw Data: {request.get_json()}")
            
            schema = LoginEmailSchema()
            data = schema.load(request.get_json())
            print(f"Validated Data: {data}")
            
            user = UserModel.query.filter(UserModel.email == data['email']).first()
            
            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()
            if not user_role:
                return jsonify({"status": False, "status_code": 404, "message": "User Role Not Found", "data": {}}), 404

            print(f"User: {user}")
            print(f"User Role: {user_role}")
            print(f"User Password Hash: {user.password_hash}")

            role = UserRoleModel.query.filter(UserRoleModel.role_id == user_role.role_id).first()
            print(f"User Role: {role.name}")

            if not bcrypt.check_password_hash(user.password_hash, data['password']):
                return jsonify({"status": False, "status_code": 400, "message": "Invalid Password", "data": {}}), 400

            print(f"User Is Active: {user.is_active}")
            print(f"User Is Verified: {user.is_verified}")

            if not user.is_active:
                return jsonify({"status": False, "status_code": 403, "message": "User is not active", "data": {}}), 403

            if not user.is_verified:
                return jsonify({"status": False, "status_code": 403, "message": "User is not verified", "data": {}}), 403

            responseSchema = UserResponseSchema()
            userData = responseSchema.dump(user)
            print(f"User Data: {userData}")

            userId = user.user_id
            print(f"User ID : {userId}")

            access_token = create_access_token(identity=userId)

            # Serialize role and accessible pages using RoleSchema
            roleSchema = RoleSchema()
            role_data = roleSchema.dump(role)  # This will include the pages for the role

            responseData = {
                "userData": userData,
                "access_token": access_token,
                "role": role_data  # Including the role and associated pages in the response
            }

            return jsonify({"status": True, "status_code": 200, "message": "User found Successfully", "data": responseData}), 200
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

@blp.route("/dashboard")
class Dashboard(MethodView):
    def get(self):
        if session or session["token"]:
            try :
                
                user_id = session["user"]
                user = UserModel.query.get(user_id)

                schema = UserResponseSchema()
                responseData = {
                    "user": schema.dump(user),
                    "role": session["user_role"]
                }
                role = session["user_role"]
                return render_template("admin/dashboard.html", error="Welcome to Dashboard", loggedUser = responseData)

            except Exception as e:
                print(f"Exception: {str(e)}")
                return redirect('/admin/auth/login?error='+{str(e)})   
        else :
            return redirect('/admin/auth/login?error=Unauthorized Access')
        

@blp.route("/change-password")
class ResetPassword(MethodView):
    def get(self):
        if session["token"]:
            try :
                
                user_id = session["user"]
                user = UserModel.query.get(user_id)

                schema = UserResponseSchema()
                responseData = {
                    "user": schema.dump(user),
                    "role": session["user_role"]
                }
                role = session["user_role"]
                return render_template("admin/reset_pass.html", error="Reset Password", loggedUser = responseData)

            except Exception as e:
                print(f"Exception: {str(e)}")
                return redirect('/admin/auth/login?error='+{str(e)})   
        else :
            return redirect('/admin/auth/login?error=Unauthorized Access')
        
    def post(self):
        if session["token"]:
            try :

                user_id = session["user"]
                user = UserModel.query.get(user_id)

                schema = UserResponseSchema()
                responseData = {
                    "user": schema.dump(user),
                    "role": session["user_role"]
                }
                role = session["user_role"]

                if request.form['password'] != request.form['confirm_password']:
                    return render_template("admin/reset_pass.html", error="Password and Confirm Password does not match", loggedUser = responseData)

                user.password_hash = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
                db.session.commit()

                return render_template("admin/reset_pass.html", error="Password Changed Successfully", loggedUser = responseData)
                
            except Exception as e:
                print(f"Exception: {str(e)}")
                return redirect('/admin/auth/change-password?error='+{str(e)})
            
@blp.route("/logout")
class Logout(MethodView):
    def post(self):
        try : 
            if session["token"]:
                session.clear()
                return redirect('/admin/auth/login')
            else :
                return redirect('/admin/auth/login?error=Unauthorized Access')

        except Exception as e:
            print(f"Exception: {str(e)}")
            return redirect('/admin/auth/login?error=Unauthorized Access')


