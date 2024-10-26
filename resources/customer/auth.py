from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas.emailauth import UserSchema, UserResponseSchema , LoginSchema, CompanyResponseSchema ,ForgotPasswordSchema, ResetPasswordSchema
from schemas.auth import RoleSchema
from marshmallow import ValidationError 
from models import UserModel , UserRoleModel , UserRoleAssignmentsModel, EmailVerification , CompanyModel , PasswordResetRequest
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt , get_jwt_identity
from utils import AuthService, send_email
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from db import db
from utils.service import AuthService
from flask_jwt_extended import create_access_token
from datetime import datetime

import secrets
bcrypt = Bcrypt()

blp = Blueprint("Auth", "auth", description="Operations to do authentication and authorization")

@blp.route("/register")
class register(MethodView):
    def post(self):
        try:
            # Validate incoming data with userSchema
            schema = UserSchema()
            data = schema.load(request.get_json())
            print(data)

            # validate the password with confirm Password
            if data['password'] != data['confirm_password']:
                return jsonify({"status" : False, "status_code" : 400,"message": "Passwords do not match",  "data" : {} }), 400
            
            # Hash the password
            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')

            user = db.session.query(UserModel).filter_by(email=data['email']).first()

            if user:
                print("User found:", user.email)
                if not user.is_verified:
                    print("User is not verified.")
                    emailData = EmailVerification.query.filter_by(user_id=user.user_id).first()
                    verification_code = AuthService.generate_4_digit_code()
                    verification_token = AuthService.generate_random_mixed_token()

                    print("Generated verification code:", verification_code)
                    print("Generated verification token:", verification_token)

                    email_data = {
                        "title": "Email Verification",
                        "body": f"Your email verification code is: {verification_code}",
                        "template": "mail/code.html",
                        "code": verification_code,
                        "token": verification_token,
                        "email": user.email,
                        "url": "http://localhost:6456/api/v1/auth/email/verify?user_id=" + str(user.user_id) + "&code=" + str(verification_code) + "&token=" + str(verification_token)
                    }

                    # If no emailData exists, create a new one
                    if not emailData:
                        print("No existing email data found, creating new.")
                        email_sent = send_email(email_data)
                        print("Email sent status:", email_sent)
                        if email_sent:
                            new_EmailToken = EmailVerification(
                                user_id=user.user_id,
                                verification_token=verification_token,
                                verification_code=verification_code,
                                sent_at=datetime.now(),
                                expires_at=datetime.now() + timedelta(hours=2),
                                is_verified=False,  # Initially False until verified
                            )
                            db.session.add(new_EmailToken)
                            db.session.commit()
                            print("New EmailVerification token saved to database.")
                        else:
                            print("Failed to send email.")
                            return jsonify({"status": False, "message": "Failed to send email."}), 500
                    else:
                        print("Existing email data found.")
                        # If emailData exists and the token has not expired
                        if emailData.expires_at > datetime.now():
                            print("Email data is still valid, sending email.")
                            email_sent = send_email(email_data)
                            print("Email sent status:", email_sent)
                            if email_sent:
                                emailData.verification_code = verification_code
                                emailData.verification_token = verification_token
                                emailData.expires_at = datetime.now() + timedelta(hours=2)
                                db.session.commit()
                                print("Email data updated with new code and token.")
                            else:
                                print("Failed to send email.")
                                return jsonify({"status": False, "message": "Failed to send email."}), 500
                        else:
                            print("Email data expired, resending existing code and token.")
                            email_data['code'] = emailData.verification_code
                            email_data['token'] = emailData.verification_token
                            email_sent = send_email(email_data)
                            print("Email sent status:", email_sent)

                        # Pass the verification code in the 'data' field
                        print("Returning response with verification code:", emailData.verification_code)
                        return jsonify({
                            "status": True, 
                            "status_code": 202, 
                            "message": "User with this email already exists but is not verified.", 
                            "data": {"verification_code": emailData.verification_code}
                        }), 202
                else:
                    # User is verified
                    print("User is already verified.")
                    return jsonify({
                        "status": False, 
                        "status_code": 409, 
                        "message": "User with this email already exists.", 
                        "data": {}
                    }), 409


            if 'phone_number' in data and data['phone_number'] is not None:
                if db.session.query(UserModel).filter_by(phone_number=data['phone_number']).first():
                    return jsonify({"status": False, "status_code": 409, "message": "User with this phone number already exists.", "data": {}}), 409

                        # Check the customer type and validate required fields for business
            
            if 'email' in data and data['email'] is not None:
                if db.session.query(UserModel).filter_by(email=data['email']).first():
                    return jsonify({"status": False, "status_code": 409, "message": "User with this email already exists.", "data": {}}), 409

            if data['customer_type'] == "Business":
                if not data.get('company_name'):
                    return jsonify({"status": False, "status_code": 400, "message": "Company name is required for business customers.", "data": {}}), 400
                if not data.get('gst_number'):
                    return jsonify({"status": False, "status_code": 400, "message": "GST number is required for business customers.", "data": {}}), 400

                # Check for existing company with the same name and GST number
                if db.session.query(CompanyModel).filter_by(name=data['company_name']).first():
                    return jsonify({"status": False, "status_code": 409, "message": "Company with this name and GST number already exists.", "data": {}}), 409
                
                # Check for existing company with the same name and GST number
                if db.session.query(CompanyModel).filter_by(gst_number=data['gst_number']).first():
                    return jsonify({"status": False, "status_code": 409, "message": "Company with this name and GST number already exists.", "data": {}}), 409

            # Create a new user instance
            new_user = UserModel(
                email=data['email'],
                password_hash=data['password'],
                name=data['name'],
                phone_number = data['phone_number'],
                customer_type=data['customer_type'],
                is_active=True,
                is_verified=False,
                is_email_verified=False,
                reset_password=False,                      
                created_at=datetime.now(),             
                updated_at=datetime.now()
            )

            db.session.add(new_user)
            db.session.commit()

            # Check the customer type
            if data['customer_type'] == "Business":

                new_company = CompanyModel(
                    name=data['company_name'],
                    gst_number=data['gst_number'],
                    user_id=new_user.user_id
                )

                db.session.add(new_company)
                db.session.commit()

            else :
                pass
                


            role = db.session.query(UserRoleModel).filter_by(name = "Customer").first()
    
            if role is None:
                return jsonify({"status" : False, "status_code" : 404,"message": "Role not found",  "data" : {} }), 404
            
            # Verify if the role is already assigned to the user
            if db.session.query(UserRoleAssignmentsModel).filter_by(user_id = new_user.user_id, role_id = role.role_id).first():
                return jsonify({"status" : False, "status_code" : 409,"message": "Role already assigned to the user",  "data" : {} }), 409

            # Add the user to the user_role_assignments table
            roleAssignment = UserRoleAssignmentsModel(user_id=new_user.user_id, role_id=role.role_id)

            db.session.add(roleAssignment)
            db.session.commit()

            # Send an email to the user
            code = AuthService.generate_4_digit_code()
            auth_token = AuthService.generate_random_mixed_token()
            email_data = {
                "title": "Email Verification",
                "body": f"Your email verification code is: {code}",
                "template": "mail/code.html",
                "code": code,
                "token" : auth_token,
                "email": new_user.email,
                "url": "http://localhost:6456/api/v1/auth/email/verify?user_id=" + str(new_user.user_id) + "&code=" + str(code) + "&token=" + str(auth_token)
            }
            print(email_data)
            email_sent = send_email(email_data)

            if not email_sent:
                return jsonify({"status": False, "status_code": 500, "message": "Failed to send verification email"}), 500

            # Update the Token in the Data Base
            new_EmailToken = EmailVerification(
                user_id = new_user.user_id,
                verification_token = auth_token,
                verification_code = code,
                sent_at = datetime.now(),
                expires_at = datetime.now() + timedelta(hours=2),
                is_verified = True,
            )

            db.session.add(new_EmailToken)
            db.session.commit()


            if new_user.customer_type == "Business":
                responseSchema = UserResponseSchema()
                userData = responseSchema.dump(new_user)

                companySchema = CompanyResponseSchema()
                companyData = companySchema.dump(new_company)
                
                responseData = {
                    "userData": userData,
                    "companyData" : companyData,
                    "role": role.name,
                    "verification_code" : code

                }

                return jsonify({"status" : True, "status_code" : 201, "message": "User created Successfully", "data": responseData}), 200
            else :
                responseSchema = UserResponseSchema()
                userData = responseSchema.dump(new_user)

                responseData = {
                    "userData": userData,
                    "role": role.name,
                    "verification_code" : code
                }

                return jsonify({"status" : True, "status_code" : 200, "message": "User created Successfully", "data": responseData}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({"status" : False, "status_code" : 500,"message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()

@blp.route("/login")
class Login(MethodView):
    def post(self):
        try:
            print(f"Raw Data: {request.get_json()}")
            
            schema = LoginSchema()
            data = schema.load(request.get_json())
            print(f"Validated Data: {data}")
            
            user = UserModel.query.filter(UserModel.email == data['email']).first()
            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()
            if not user_role:
                return jsonify({"status": False, "status_code": 404, "message": "User Role Not Found", "data": {}}), 404

            print(f"User: {user}")
            print(f"User Password Hash: {user.password_hash}")

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

            responseData = {
                "userData": userData,
                "access_token": access_token,
                "role" : user_role.role.name
            }

            return jsonify({"status": True, "status_code": 200, "message": "User found Successfully", "data": responseData}), 200
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500        


@blp.route("/verify/<int:user_id>")
class VerifyUser(MethodView):
    @jwt_required()
    def post(self, user_id):
        try:
            user = UserModel.query.filter(UserModel.user_id == user_id).first()

            jwt = get_jwt()
            print(f"JWT Claims received: {jwt}")

            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            user.is_verified = True
            db.session.commit()

            return jsonify({"status": True, "status_code": 200, "message": "User Verified Successfully", "data": {}}), 200

        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
    
@blp.route("/resend-email-verification")
class ResendEmailVerification(MethodView):
    def post(self):
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({"status": False, "status_code": 400, "message": "Email is required", "data": {}}), 400
            
            userData = UserModel.query.filter(UserModel.email == data['email']).first()

            if not userData:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            if userData.is_verified and userData.is_email_verified:
                return jsonify({"status": False, "status_code": 200, "message": "User Already Verified", "data": {}}), 200

            emailData = EmailVerification.query.filter(EmailVerification.user_id == userData.user_id).first()

            if not emailData:
                code = AuthService.generate_4_digit_code()
                auth_token = AuthService.generate_random_mixed_token()
                email_data = {
                    "title": "Email Verification",
                    "body": f"Your email verification code is: {code}",
                    "template": "/mail/code.html",
                    "code": code,
                    "token" : auth_token,
                    "email": userData.email,
                    "url": "http://localhost:6456/api/v1/auth/email/verify?user_id=" + str(userData.user_id) + "&code=" + str(code) + "&token=" + str(auth_token)
                }
                print(email_data)
                email_sent = send_email(email_data)

                if not email_sent:
                    return jsonify({"status": False, "status_code": 500, "message": "Failed to send verification email"}), 500

                # Update the Token in the Data Base
                new_EmailToken = EmailVerification(
                    user_id = userData.user_id,
                    verification_token = auth_token,
                    verification_code = code,
                    sent_at = datetime.now(),
                    expires_at = datetime.now() + timedelta(hours=2),
                    is_verified = True,
                )

                db.session.add(new_EmailToken)
                db.session.commit()

            else :
                email_data = {
                    "title": "Email Verification",
                    "body": f"Your email verification code is: {emailData.verification_code}",
                    "template": "mail/code.html",
                    "code": emailData.verification_code,
                    "token" : emailData.verification_token,
                    "email": userData.email,
                    "url": "http://localhost:6456/api/v1/auth/email/verify?user_id=" + str(userData.user_id)+"&code=" + str(emailData.verification_code)+"&token=" + str(emailData.verification_token)
                }
                print(email_data)
                email_sent = send_email(email_data)

                if not email_sent:
                    return jsonify({"status": False, "status_code": 500, "message": "Failed to send verification email"}), 500

            return jsonify({"status": True, "status_code": 200, "message": "Email Sent Successfully", "data": {}}), 200

        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()


@blp.route("/verify")
class VerifyEmail(MethodView):
    def get(self):
        try:
            user_id = request.args.get("user_id")
            
            if not user_id:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401
            
            user_data = UserModel.query.filter_by(user_id=user_id).first()

            if not user_data:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            if user_data.is_verified and user_data.is_email_verified:
                return jsonify({"status": False, "status_code": 200, "message": "User Already Verified", "data": {}}), 200

            # Fetch email verification data
            email_data = EmailVerification.query.filter_by(user_id=user_id).first()

            if not email_data:
                return jsonify({"status": False, "status_code": 404, "message": "Verification Token Not Found", "data": {}}), 404
            
            # Validate token and code
            token = request.args.get("token")
            code = request.args.get("code")
            
            print(f"Token: {token}, Code: {code}")
            print(f"Stored Token: {email_data.verification_token}, Stored Code: {email_data.verification_code}") 
            if email_data.verification_token != token:
                return jsonify({"status": False, "status_code": 401, "message": "Invalid Token", "data": {}}), 401

            if email_data.verification_code != int(code):
                return jsonify({"status": False, "status_code": 401, "message": "Invalid Verification Code", "data": {}}), 401
            
            # Update user verification status
            user_data.is_verified = True
            user_data.is_email_verified = True
            db.session.commit()

            db.session.delete(email_data)
            db.session.commit()

            user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user_data.user_id).first()

            if not user_role:
                return jsonify({
                    "status": False,
                    "status_code": 404,
                    "message": "User role is not assigned.",
                    "data": {}
                }), 404

            # Fetch the role
            role = UserRoleModel.query.filter(UserRoleModel.role_id == user_role.role_id).first()

            if not role:
                return jsonify({
                    "status": False,
                    "status_code": 404,
                    "message": "User role not found.",
                    "data": {}
                }), 404
            
            # if not role.name == "Customer":
            #     return jsonify({
            #         "status": False,
            #         "status_code": 400,
            #         "message": "User is unauthorized.",
            #         "data": {}
            #     }), 400
            # Generate JWT access token
            access_token = create_access_token(identity=user_data.user_id)
            roleSchema = RoleSchema()
            role_data = roleSchema.dump(role)  # This will include the pages for the role
        

            responseSchema = UserResponseSchema()
            userData = responseSchema.dump(user_data)

            responseData = {
                "userData": userData,
                "access_token": access_token,
                "role": role_data
            }

            return jsonify({"status": True, "status_code": 200, "message": "User Verified Successfully", "data": responseData}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()

    def post(self):
        try:
            data = request.get_json()
            email = data.get("email")

            if not data or not data.get("otp"):
                return jsonify({"status": False, "status_code": 400, "message": "OTP is required", "data": {}}), 400
            
            otp = int(data.get("otp"))

            user_data = UserModel.query.filter_by(email=email).first()

            if not user_data:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            if user_data.is_verified and user_data.is_email_verified:
                return jsonify({"status": False, "status_code": 200, "message": "User Already Verified", "data": {}}), 200

            # Fetch email verification data
            email_data = EmailVerification.query.filter_by(user_id=user_data.user_id).first()

            if not email_data:
                return jsonify({"status": False, "status_code": 404, "message": "Verification Token Not Found", "data": {}}), 404
            
            if email_data.verification_code != otp:
                return jsonify({"status": False, "status_code": 401, "message": "Invalid OTP", "data": {}}), 401
            
            # Update user verification status
            user_data.is_verified = True
            user_data.is_email_verified = True
            db.session.commit()

            db.session.delete(email_data)
            db.session.commit()

            role_assign = UserRoleAssignmentsModel.query.filter_by(user_id=user_data.user_id).first()

            if not role_assign:
                return jsonify({"status": False, "status_code": 404, "message": "Role Not Found", "data": {}}), 404
            
            role = UserRoleModel.query.filter_by(role_id=role_assign.role_id).first()

            if not role:
                return jsonify({"status": False, "status_code": 404, "message": "Role Not Found", "data": {}}), 404
            
            user_data.role = role.name


            responseSchema = UserResponseSchema()
            userData = responseSchema.dump(user_data)
            access_token = create_access_token(identity=user_data.user_id)

            responseData = {
                "userData": userData,
                "role" : user_data.role,
                "access_token": access_token
            }
            return jsonify({"status": True, "status_code": 200, "message": "User Verified Successfully", "data": responseData}), 200
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()

@blp.route("/forgot-password")
class ForgotPassword(MethodView):
    def post(self):
        try:
            data = request.get_json()
            email = data["email"]

            if not email:
                return jsonify({"status": False, "status_code": 400, "message": "Email is required", "data": {}}), 400
            
            user_data = UserModel.query.filter_by(email=email).first()

            if not user_data:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
            
            if not user_data.is_active:
                return jsonify({"status": False, "status_code": 401, "message": "User is Inactive", "data": {}}), 401
            
            # Generate verification code
            passwordRequest = PasswordResetRequest.query.filter_by(user_id=user_data.user_id).first()
            code = AuthService.generate_4_digit_code()
            auth_token = AuthService.generate_random_mixed_token()

            if passwordRequest:
                if passwordRequest.expires_at < datetime.now():
                    print("Time Exceeds")
                    email_data = {
                        "title": "Warranty - Reset Forgotten Password",
                        "body": f"Please click below to reset your password for Warranty Support.",
                        "template": "mail/forgot-password.html",
                        "code": code,
                        "token" : auth_token,
                        "email": user_data.email,
                        "url": "http://localhost:6456/api/v1/auth/email/forgot-password?user_id=" + str(user_data.email) + "&code=" + str(code) + "&token=" + str(auth_token)
                    }
                    print(email_data)

                    passwordRequest.reset_code = email_data['code']
                    passwordRequest.reset_token = email_data['token']
                    passwordRequest.expires_at = datetime.now() + timedelta(minutes=120)

                    db.session.add(passwordRequest)
                    db.session.commit()

                    email_sent = send_email(email_data)



                    if not email_sent:
                        return jsonify({"status": False, "status_code": 500, "message": "Failed to send verification email"}), 500

                    return jsonify({"status": True, "status_code": 200, "message": "Request Sent Successfully", "data": { "verification_code" : passwordRequest.reset_code }}), 200 
                else: 
                    email_data = {
                        "title": "Warranty - Reset Forgotten Password",
                        "body": f"Please click below to reset your password for Warranty Support.",
                        "template": "mail/forgot-password.html",
                        "code": passwordRequest.reset_code,
                        "token" : passwordRequest.reset_token,
                        "email": user_data.email,
                        "url": "http://localhost:6456/api/v1/auth/email/forgot-password?user_id=" + str(user_data.email) + "&code=" + str(passwordRequest.reset_code) + "&token=" + str(passwordRequest.reset_token)
                    }
                    print(email_data)
                    email_sent = send_email(email_data)

                    if not email_sent:
                        return jsonify({"status": False, "status_code": 500, "message": "Failed to send verification email"}), 500

                    return jsonify({"status": True, "status_code": 200, "message": "Request Sent Successfully", "data": { "verification_code" : passwordRequest.reset_code }}), 200 


            email_data = {
                    "title": "Warranty - Reset Forgotten Password",
                    "body": f"Please click below to reset your password for Warranty Support.",
                    "template": "mail/forgot-password.html",
                    "code": code,
                    "token" : auth_token,
                    "email": user_data.email,
                    "url": "http://localhost:6456/api/v1/auth/email/forgot-password?user_id=" + str(user_data.email) + "&code=" + str(code) + "&token=" + str(auth_token)
                }
            
            print(email_data)

            requestData = {
                "user_id": user_data.user_id,
                "reset_token" : auth_token,
                "reset_code": code,
                "requested_at" : datetime.now(), 
                "expires_at" : datetime.now() + timedelta(minutes=120),
            }

            passwordRequest = PasswordResetRequest(**requestData)
            db.session.add(passwordRequest)
            db.session.commit()
            
            email_sent = send_email(email_data)

            if email_sent:
                return jsonify({"status": True, "status_code": 200, "message": "Request Sent Successfully", "data": {"verification_code" : passwordRequest.reset_code }}), 200
            
        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()
            
        
@blp.route("/forgot-password/verify")
class ForgotPasswordVerify(MethodView):
    def post(self):
        try:
            schema = ForgotPasswordSchema()
            data = schema.load(request.get_json())
            print(data)

            if not data:
                return jsonify({"status": False, "status_code": 400, "message": "All fields are required", "data": {}}), 400

            user = UserModel.query.filter_by(email=data['email']).first()

            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404
                    
            passwordRequest = PasswordResetRequest.query.filter_by(user_id=user.user_id, reset_code=data['code']).first()

            if not passwordRequest:
                return jsonify({"status": False, "status_code": 404, "message": "Request Not Found", "data": {}}), 404
            
            if passwordRequest.expires_at < datetime.now():
                return jsonify({"status": False, "status_code": 401, "message": "Request Expired", "data": {}}), 401
            
            # validate code 
            if passwordRequest.reset_code != data['code']:
                return jsonify({"status": False, "status_code": 401, "message": "Invalid Code", "data": {}}), 401

            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            user.password = data['password']
            user.reset_password = False
            db.session.commit()

            db.session.delete(passwordRequest)
            db.session.commit()
            

            return jsonify({"status": True, "status_code": 200, "message": "Password Reset Successfully", "data": {}}), 200 

        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()


@blp.route("/reset-password")
class ResetPassword(MethodView):
    @jwt_required()
    def post(self):
        try:
            schema = ResetPasswordSchema()
            data = schema.load(request.get_json())
            print(data)

            if not data:
                return jsonify({"status": False, "status_code": 400, "message": "All fields are required", "data": {}}), 400

            user = UserModel.query.filter_by(email=data['email']).first()

            if not user:
                return jsonify({"status": False, "status_code": 404, "message": "User Not Found", "data": {}}), 404

            if user.is_verified == False or user.is_email_verified == False:
                return jsonify({"status": False, "status_code": 401, "message": "User Not Verified", "data": {}}), 401

            if user.reset_password == False:
                return jsonify({"status": False, "status_code": 401, "message": "User Not Allowed", "data": {}}), 401
            
            # Validate password and confirm password
            if data['password'] != data['confirm_password']:
                return jsonify({"status": False, "status_code": 401, "message": "Password and Confirm Password does not match", "data": {}}), 401
            
            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            user.password = data['password']
            user.reset_password = False
            db.session.commit()

            return jsonify({"status": True, "status_code": 200, "message": "Password Reset Successfully", "data": {}}), 200 

        except Exception as e:
            print(f"Exception: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500
        
        finally:
            db.session.close()