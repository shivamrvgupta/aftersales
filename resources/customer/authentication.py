from flask_restful import Resource
import logging
import re
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from twilio.rest import Client
from schemas.auth import UserSchema, UserResponseSchema , LoginSchema, CompanyResponseSchema ,ForgotPasswordSchema, RoleSchema
from schemas.warranty import WarrantyResponseSchema
from models import UserModel , UserRoleModel , UserRoleAssignmentsModel, EmailVerification , CompanyModel , PasswordResetRequest , OtpVerification
import models
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt , get_jwt_identity
from utils import handle_otp
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
from db import db
from utils.service import AuthService
from flask_jwt_extended import create_access_token
from datetime import datetime

client = Client(account_sid, auth_token)

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import secrets
bcrypt = Bcrypt()

blp = Blueprint("Authentication", "authentication", description="Operations to do authentication and authorization using phone number")



# SendOTP Class
@blp.route("/send-otp")
class SendOTP(MethodView):
    def post(self):
        try:
            # Log raw request data
            raw_data = request.get_json()
            logger.info(f"Raw Data: {raw_data}")

            # Load and validate input data
            schema = LoginSchema()
            data = schema.load(raw_data)
            logger.info(f"Parsed and validated data: {data}")

            if not data.get('phone_number'):
                logger.warning("Phone number is missing or empty.")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Phone number is required",
                    "data": {}
                }), 400

            # Normalize the phone number using AuthService
            normalized_phone_number = AuthService.normalize_phone_number(data['phone_number'])
            logger.info(f"Normalized Phone Number: {normalized_phone_number}")

            # Regular expression to match a normalized 10-digit phone number
            phone_pattern = r'^\d{10}$'

            if not re.match(phone_pattern, normalized_phone_number):
                logger.warning(f"Invalid phone number format: {normalized_phone_number}")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Invalid phone number format. It should be 10 digits.",
                    "data": {}
                }), 400

            # Attempt to fetch the user by normalized phone number
            user = UserModel.query.filter(UserModel.phone_number == normalized_phone_number).first()
            if user:
                logger.info(f"User fetched: {user}")
                user_found_message = 'User Found and OTP sent successfully'
            else:
                logger.warning(f"User not found with phone number: {normalized_phone_number} - OTP will still be sent")
                user_found_message = 'User Not Found, Please register first.'

            # Call the handle_otp function to process and return the OTP
            otp = handle_otp(normalized_phone_number)

            # Create and send the SMS message
            message_instance = client.messages.create(
                from_='+19715992795',  # Use 'from_' instead of 'from'
                body=f'Your OTP code is: {otp}',  # Use the generated OTP in the message
                to='+91' + normalized_phone_number
            )

            # Prepare response data with relevant info
            responseData = {
                "phone_number": normalized_phone_number,
                "otp": otp
            }

            logger.info(f"Returning response: {responseData}")
            return jsonify({
                "status": True, 
                "status_code": 200, 
                "message": user_found_message, 
                "data": responseData
            }), 200

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return jsonify({"status": False, "status_code": 500, "message": "An error occurred", "error": str(e)}), 500

        finally:
            db.session.close()
            logger.info("Database session closed.")

# VerifyOTP Class
@blp.route("/verify-otp")
class VerifyOTP(MethodView):
    def post(self):
        try:
            # Log raw request data
            raw_data = request.get_json()
            logger.info(f"Raw Data: {raw_data}")

            # Validate the input data (phone number and OTP)
            phone_number = raw_data.get('phone_number')
            entered_otp = raw_data.get('otp')

            if not phone_number or not entered_otp:
                logger.warning("Missing phone number or OTP")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Phone number and OTP are required."
                }), 400

            # Normalize the phone number using AuthService
            normalized_phone_number = AuthService.normalize_phone_number(phone_number)
            logger.info(f"Normalized Phone Number: {normalized_phone_number}")

            # Regular expression to match a normalized 10-digit phone number
            phone_pattern = r'^\d{10}$'

            if not re.match(phone_pattern, normalized_phone_number):
                logger.warning(f"Invalid phone number format: {normalized_phone_number}")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Invalid phone number format. It should be 10 digits.",
                    "data": {}
                }), 400
                
            # Fetch the OTP from the system
            otp_record = OtpVerification.query.filter_by(phone_number=normalized_phone_number, otp=entered_otp).first()

            if not otp_record:
                logger.warning(f"Invalid OTP for phone number: {normalized_phone_number}")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Invalid OTP.",
                    "data": {}
                }), 400

            # Check if the OTP is expired
            if otp_record.expires_at < datetime.now(): 
                logger.warning(f"OTP expired for phone number: {normalized_phone_number}")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "OTP has expired.",
                    "data": {}
                }), 400

            # Check if the user is registered
            user = UserModel.query.filter_by(phone_number=normalized_phone_number).first()

            if not user:
                logger.warning(f"User not found with phone number: {normalized_phone_number}")
                return jsonify({
                    "status": True,
                    "status_code": 200,
                    "message": "Mobile Number verified successfully, Please Register first.",
                    "data": {}
                }), 200
            else:
                # Serialize user data
                responseSchema = UserResponseSchema()
                userData = responseSchema.dump(user)  

                # Check the user is active or not 
                if not user.is_active or not user.is_verified:
                    return jsonify({
                            "data": {},
                            "message": "User is not verified",
                            "status": False,
                            "status_code": 403
                    }), 400
                
                # Check if the user has a role assigned
                user_role = UserRoleAssignmentsModel.query.filter(UserRoleAssignmentsModel.user_id == user.user_id).first()

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
                access_token = create_access_token(identity=user.user_id)
                roleSchema = RoleSchema()
                role_data = roleSchema.dump(role)  # This will include the pages for the role
                # check the user Type   
                if user.customer_type == "Business":
                    company = CompanyModel.query.filter(CompanyModel.user_id == user.user_id).first()
                    company_schema = CompanyResponseSchema()
                    company_data = company_schema.dump(company)
                    response_data = {
                        "user": userData,
                        "company": company_data,
                        "role": role_data,
                        "access_token" : access_token
                    }
                    logger.info(f"Business user {user.phone_number} Logged in successfully.")
                    return jsonify({"status": True, "status_code": 201, "message": "User authenticated successfully.", "data": response_data}), 201
                else:
                    response_data = {
                        "userData": userData,
                        "access_token": access_token,
                        "role" : role_data
                    }
                    logger.info(f"Customer user created successfully.")
                    return jsonify({"status": True, "status_code": 200, "message": "User authenticated successfully.", "data": response_data}), 200

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}", exc_info=True)
            return jsonify({
                "status": False,
                "status_code": 500,
                "message": "An error occurred during OTP validation.",
                "error": str(e)
            }), 500

        finally:
            db.session.close()
            logger.info("Database session closed.")

@blp.route("/register")
class Register(MethodView):
    def post(self):
        try:
            # Log raw request data
            raw_data = request.get_json()
            logger.info(f"Received raw data: {raw_data}")

            # Validate the input data
            schema = UserSchema()
            data = schema.load(raw_data)

            # Check if the data is valid
            if not data:
                logger.warning("Invalid data provided in the request.")
                return jsonify({
                    "status": False,
                    "status_code": 400,
                    "message": "Invalid data",
                    "data": {}
                }), 400

            # Check if the user is already registered
            user = UserModel.query.filter_by(phone_number=data['phone_number']).first()
            if user:
                logger.warning(f"User already registered with phone number: {data['phone_number']}")
                return jsonify({
                    "status": True,
                    "status_code": 200,  # Return 200 to indicate the user is already registered
                    "message": "User already registered.",
                    "data": {}
                }), 200

            email = data.get('email')  # Safely handle the absence of the 'email' field
            if email:
                user = UserModel.query.filter_by(email=email).first()
                if user:
                    logger.warning(f"User already registered with email: {email}")
                    return jsonify({
                        "status": True,
                        "status_code": 200,  # Return 200 to indicate the user is already registered
                        "message": "User already registered.",
                        "data": {}
                    }), 200
                
            # Check for customer type and required fields
            if data['customer_type'] == "Business":
                if not data.get('company_name'):
                    logger.warning("Business customer without company name.")
                    return jsonify({
                        "status": False,
                        "status_code": 400,
                        "message": "Company name is required for business customers.",
                        "data": {}
                    }), 400
                if not data.get('gst_number'):
                    logger.warning("Business customer without GST number.")
                    return jsonify({
                        "status": False,
                        "status_code": 400,
                        "message": "GST number is required for business customers.",
                        "data": {}
                    }), 400

                # Check for existing company with the same name or GST number
                if db.session.query(CompanyModel).filter_by(name=data['company_name']).first():
                    logger.warning(f"Company with the name {data['company_name']} already exists.")
                    return jsonify({
                        "status": False,
                        "status_code": 409,
                        "message": "Company with this name already exists.",
                        "data": {}
                    }), 409
                
                if db.session.query(CompanyModel).filter_by(gst_number=data['gst_number']).first():
                    logger.warning(f"Company with the GST number {data['gst_number']} already exists.")
                    return jsonify({
                        "status": False,
                        "status_code": 409,
                        "message": "Company with this GST number already exists.",
                        "data": {}
                    }), 409

            # Create a new user instance
            new_user = UserModel(
                name=data['name'],
                customer_type=data['customer_type'],
                phone_number=data['phone_number'],
                password_hash=None,  
                email=email if email else None,
                is_active=True,
                is_verified=True,
                is_email_verified = False,
                reset_password = True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.info(f"Creating new user: {data['phone_number']}")

            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"User {new_user.phone_number} created successfully.")

            # If the customer type is Business, create a new company instance
            if data['customer_type'] == "Business":
                new_company = CompanyModel(
                    name=data['company_name'],
                    gst_number=data['gst_number'],
                    user_id=new_user.user_id
                )
                db.session.add(new_company)
                db.session.commit()
                logger.info(f"Company {new_company.name} created successfully.")

            # Assign the "Customer" role to the user
            role = db.session.query(UserRoleModel).filter_by(name="Customer").first()
            if not role:
                logger.error("Role 'Customer' not found in the database.")
                return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}}), 404
            
            # Verify if the role is already assigned
            if db.session.query(UserRoleAssignmentsModel).filter_by(user_id=new_user.user_id, role_id=role.role_id).first():
                logger.warning(f"Role 'Customer' already assigned to user {new_user.phone_number}.")
                return jsonify({"status": False, "status_code": 409, "message": "Role already assigned to the user", "data": {}}), 409

            # Assign the role to the user
            role_assignment = UserRoleAssignmentsModel(user_id=new_user.user_id, role_id=role.role_id)
            db.session.add(role_assignment)
            db.session.commit()
            logger.info(f"Role 'Customer' assigned to user {new_user.phone_number}.")

        
            message = client.messages.create(
                from_='whatsapp:+14155238886',
                content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
                content_variables='{"1":"12/1","2":"3pm"}',
                to='whatsapp:+91' + str(new_user.phone_number)
            )

            print(message.sid)

            # Prepare response data
            response_schema = UserResponseSchema()
            user_data = response_schema.dump(new_user)

            access_token = create_access_token(identity=new_user.user_id)

            if new_user.customer_type == "Business":
                company_schema = CompanyResponseSchema()
                company_data = company_schema.dump(new_company)
                response_data = {
                    "user": user_data,
                    "company": company_data,
                    "role": role.name,
                    "access_token": access_token
                }
                logger.info(f"Business user {new_user.phone_number} created successfully.")
                return jsonify({
                    "status": True,
                    "status_code": 201,
                    "message": "User created successfully",
                    "data": response_data
                }), 201
            else:
                response_data = {
                    "user": user_data,
                    "role": role.name,
                    "access_token": access_token
                }
                logger.info(f"Customer user {new_user.phone_number} created successfully.")
                return jsonify({
                    "status": True,
                    "status_code": 200,
                    "message": "User created successfully",
                    "data": response_data
                }), 200

        except Exception as e:
            logger.error(f"Error occurred while registering user: {str(e)}")
            return jsonify({
                "status": False,
                "status_code": 500,
                "message": "Internal server error",
                "data": {}
            }), 500

        finally:
            db.session.close()

@blp.route("/dashboard")
class Dashboard(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()
            logger.info(f"JWT payload: {jwt}")
            
            if jwt.get("role") not in ["Customer", "Admin"]:
                return jsonify({
                    "status": False,
                    "status_code": 401,
                    "message": "Unauthorized Access",
                    "data": {}
                }), 401

            user_id = jwt.get("user_id")
            logger.info(f"User ID from JWT: {user_id}")

            # Fetch all warranties for the customer
            warranties = models.WarrantyModel.query.filter_by(customer_id=user_id).all()
            logger.info(f"Fetched warranties: {warranties}")

            if not warranties:
                return jsonify({
                    "status": True,
                    "status_code": 200,
                    "message": "No Warranties Found",
                    "data": {"active_count": 0, "expired_count": 0, "pending_count": 0, "completed_count": 0}
                }), 200

            active_count = 0
            expired_count = 0
            pending_count = 0
            completed_count = 0

            current_date = datetime.now().date()

            # Count active and expired warranties based on the warranty status
            for warranty in warranties:
                logger.info(f"Processing warranty with end date {warranty.warranty_end_date}")
                if warranty.warranty_end_date >= current_date:
                    active_count += 1
                else:
                    expired_count += 1

            # Return only the counts
            return jsonify({
                'status': True,
                'status_code': 200,
                'message': 'Warranty counts fetched successfully',
                'data': {
                    'active_count': active_count,
                    'expired_count': expired_count,
                    'pending_count': pending_count,
                    'completed_count': completed_count
                }
            }), 200

        except Exception as e:
            logger.error(f"Error occurred while fetching warranty counts: {str(e)}")
            return jsonify({
                "status": False,
                "status_code": 500,
                "message": "Internal Server Error",
                "data": {"error": str(e)}
            }), 500
        finally:
            db.session.close()

