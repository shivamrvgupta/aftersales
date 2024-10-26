from flask import request, jsonify
from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
import models
import logging
from sqlalchemy.orm import Session
from flask_jwt_extended import jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from db import db
from datetime import datetime
from utils import AuthService
from utils.email import send_email_warranty

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bcrypt = Bcrypt()

blp = Blueprint("General", "general", description="Operations to check manage things without JWT")

@blp.route("/add-sale")
class AddSale(MethodView):
    def post(self):
        try: 
            data = request.json
            logger.info("Request received to add sale")

            # Check for required fields in the request data
            required_fields = ['user', 'address', 'product']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required", "data": {}}), 400

            # User data validation
            user_data = data['user']
            user = db.session.query(models.UserModel).filter_by(phone_number=user_data['phone_number']).first()
            logger.info(f"Checking if user with phone number {user_data['phone_number']} exists")
            
            user_required_fields = ['name', 'customer_type', 'phone_number']
            for field in user_required_fields:
                if field not in user_data:
                    logger.warning(f"Missing user field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for Individual customers.", "data": {}}), 400
                        
            # If user does not exist, create a new one
            if not user:
                logger.info("User does not exist, creating a new user")
                
                # Validate business customer details if the customer type is "Business"
                if user_data['customer_type'] == "Business":
                    logger.info("Processing business customer")
                    user_required_fields = ['name', 'customer_type', 'phone_number', 'company_name', 'gst_number']
                    for field in user_required_fields:
                        if field not in user_data:
                            logger.warning(f"Missing business customer field: {field}")
                            return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for business customers.", "data": {}}), 400

                    if not user_data.get('company_name'):
                        logger.warning("Business customer without company name.")
                        return jsonify({"status": False, "status_code": 400, "message": "Company name is required for business customers.", "data": {}}), 400
                    if not user_data.get('gst_number'):
                        logger.warning("Business customer without GST number.")
                        return jsonify({"status": False, "status_code": 400, "message": "GST number is required for business customers.", "data": {}}), 400

                    # Check for existing company with the same name or GST number
                    if db.session.query(models.CompanyModel).filter_by(name=user_data['company_name']).first():
                        logger.warning(f"Company with the name {user_data['company_name']} already exists.")
                        return jsonify({"status": False, "status_code": 409, "message": "Company with this name already exists.", "data": {}}), 409
                    
                    if db.session.query(models.CompanyModel).filter_by(gst_number=user_data['gst_number']).first():
                        logger.warning(f"Company with the GST number {user_data['gst_number']} already exists.")
                        return jsonify({"status": False, "status_code": 409, "message": "Company with this GST number already exists.", "data": {}}), 409

                # Create a new user instance
                user = models.UserModel(
                    name=user_data['name'],
                    customer_type=user_data['customer_type'],
                    phone_number=user_data['phone_number'],
                    email=user_data.get('email', ""),
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                logger.info(f"Creating new user: {user_data['phone_number']}")

                # Add the new user to the database
                db.session.add(user)
                db.session.commit()
                logger.info(f"User {user.phone_number} created successfully.")

                # If the customer type is Business, create a new company instance
                if user_data['customer_type'] == "Business":
                    new_company = models.CompanyModel(
                        name=user_data['company_name'],
                        gst_number=user_data['gst_number'],
                        user_id=user.user_id
                    )
                    db.session.add(new_company)
                    db.session.commit()
                    logger.info(f"Company {new_company.name} created successfully.")

                # Assign the "Customer" role to the user
                role = db.session.query(models.UserRoleModel).filter_by(name="Customer").first()
                if not role:
                    logger.error("Role 'Customer' not found in the database.")
                    return jsonify({"status": False, "status_code": 404, "message": "Role not found", "data": {}}), 404
                
                # Verify if the role is already assigned
                if db.session.query(models.UserRoleAssignmentsModel).filter_by(user_id=user.user_id, role_id=role.role_id).first():
                    logger.warning(f"Role 'Customer' already assigned to user {user.phone_number}.")
                    return jsonify({"status": False, "status_code": 409, "message": "Role already assigned to the user", "data": {}}), 409

                # Assign the role to the user
                role_assignment = models.UserRoleAssignmentsModel(user_id=user.user_id, role_id=role.role_id)
                db.session.add(role_assignment)
                db.session.commit()
                logger.info(f"Role 'Customer' assigned to user {user.phone_number}.")

                pass
            
            ## Add Address
            address_data = data['address']
            logger.info("Adding address for the user")

            address_required_fields = ['address_1', 'address_2', 'city', 'state', 'country', 'pincode']
            for field in address_required_fields:
                if field not in address_data:
                    logger.warning(f"Missing address field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for address.", "data": {}}), 400

            # Check for existing address
            userAddress = db.session.query(models.UserAddressModel).filter_by(
                user_id=user.user_id,
                address_1=address_data['address_1'],
                address_2=address_data['address_2'],
                city=address_data['city'],
                state=address_data['state'],
                country=address_data['country'],
                pincode=address_data['pincode']
            ).first()
            
            if not userAddress:
                userAddress = models.UserAddressModel(user_id=user.user_id, **address_data)
                db.session.add(userAddress)
                db.session.commit()

                logger.info("Address added successfully")
                return userAddress

            # Add Product
            product_data = data['product']
            logger.info("Adding product")

            product_required_fields = ['name', 'type', 'model', 'capacity', 'warranty', 'warranty_period', 'serial_no', 'unique_no', 'date_of_manufacture']
            for field in product_required_fields:
                if field not in product_data:
                    logger.warning(f"Missing product field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for product.", "data": {}}), 400

            # Check if serial_no and unique_no are already in use
            existing_product_serial = models.ProductModel.query.filter_by(serial_no=product_data['serial_no']).first()
            if existing_product_serial:
                logger.warning(f"Product with serial number {product_data['serial_no']} already exists")
                return jsonify({'status': False, 'status_code': 400, 'message': 'Serial number already exists', 'data': {}}), 400

            existing_product_unique = models.ProductModel.query.filter_by(unique_no=product_data['unique_no']).first()
            if existing_product_unique:
                logger.warning(f"Product with unique number {product_data['unique_no']} already exists")
                return jsonify({'status': False, 'status_code': 400, 'message': 'Unique number already exists', 'data': {}}), 400

            # Parse and validate the manufacture date
            try:
                manufacture_date = datetime.strptime(product_data['date_of_manufacture'], "%d-%m-%Y").date()
                logger.info(f"Validated manufacture date: {manufacture_date}")
            except ValueError:
                logger.error("Invalid date format for date_of_manufacture")
                return jsonify({'status': False, 'status_code': 400, 'message': 'Invalid date format', 'data': {}}), 400

            # Create new product
            new_product = models.ProductModel(
                name=product_data['name'],
                type=product_data['type'],
                model=product_data['model'],
                capacity=product_data['capacity'],
                warranty=product_data['warranty'],
                warranty_period=product_data['warranty_period'],
                serial_no=product_data['serial_no'],
                unique_no=product_data['unique_no'],
                date_of_manufacture=manufacture_date
            )

            db.session.add(new_product)
            db.session.commit()
            logger.info(f"Product {new_product.name} added successfully")
            
            return jsonify({'status': True, 'status_code': 201, 'message': 'Product Added Successfully', 'data': {}}), 201
        
        except Exception as e:
            logger.error(f"Error occurred while adding sale: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "Internal server error", "data": {}}), 500
        
        finally:
            db.session.close()
    
@blp.route("/register-warranty")
class AddWarranty(MethodView):
    def post(self):
        try:
            data = request.get_json()  # Changed this to explicitly get the JSON data
            print("Received Data:", data)  # Print the received data for debugging

            logger.info("Request received to register warranty")

            # Check for required fields in the request data
            required_fields = ['user', 'address', 'product']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required", "data": {}}), 400

            # User data validation
            user_data = data['user']
            user = db.session.query(models.UserModel).filter_by(phone_number=user_data['phone_number']).first()
            logger.info(f"Checking if user with phone number {user_data['phone_number']} exists")
            
            user_required_fields = ['name', 'customer_type', 'phone_number']
            for field in user_required_fields:
                if field not in user_data:
                    logger.warning(f"Missing user field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for Individual customers.", "data": {}}), 400
            
            # If user does not exist, create a new one
            if not user:
                logger.info("User does not exist, creating a new user")

                # Validate business customer details if the customer type is "Business"
                if user_data['customer_type'] == "Business":
                    logger.info("Processing business customer")
                    user_required_fields = ['name', 'customer_type', 'phone_number', 'company_name', 'gst_number']
                    for field in user_required_fields:
                        if field not in user_data:
                            logger.warning(f"Missing business customer field: {field}")
                            return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for business customers.", "data": {}}), 400

                    # Check for existing company with the same name or GST number
                    if db.session.query(models.CompanyModel).filter_by(name=user_data['company_name']).first():
                        logger.warning(f"Company with the name {user_data['company_name']} already exists.")
                        return jsonify({"status": False, "status_code": 409, "message": "Company with this name already exists.", "data": {}}), 409
                    
                    if db.session.query(models.CompanyModel).filter_by(gst_number=user_data['gst_number']).first():
                        logger.warning(f"Company with the GST number {user_data['gst_number']} already exists.")
                        return jsonify({"status": False, "status_code": 409, "message": "Company with this GST number already exists.", "data": {}}), 409

                # Create a new user instance
                user = models.UserModel(
                    name=user_data['name'],
                    customer_type=user_data['customer_type'],
                    phone_number=user_data['phone_number'],
                    email=user_data.get('email', ""),
                    is_active=True,
                    is_verified=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                logger.info(f"Creating new user: {user_data['phone_number']}")

                db.session.add(user)
                db.session.commit()
                logger.info(f"User {user.phone_number} created successfully.")

                # If the customer type is Business, create a new company instance
                if user_data['customer_type'] == "Business":
                    new_company = models.CompanyModel(
                        name=user_data['company_name'],
                        gst_number=user_data['gst_number'],
                        user_id=user.user_id
                    )
                    db.session.add(new_company)
                    db.session.commit()
                    logger.info(f"Company {new_company.name} created successfully.")

            # Add Address
            address_data = data['address']
            logger.info("Adding address for the user")

            address_required_fields = ['address_1', 'address_2', 'city', 'state', 'country', 'pincode']
            for field in address_required_fields:
                if field not in address_data:
                    logger.warning(f"Missing address field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for address.", "data": {}}), 400

            # Check for existing address
            user_address = db.session.query(models.UserAddressModel).filter_by(
                user_id=user.user_id,
                address_1=address_data['address_1'],
                address_2=address_data['address_2'],
                city=address_data['city'],
                state=address_data['state'],
                country=address_data['country'],
                pincode=address_data['pincode']
            ).first()
            
            if not user_address:
                user_address = models.UserAddressModel(user_id=user.user_id, **address_data)
                db.session.add(user_address)
                db.session.commit()

                logger.info("Address added successfully")

            # **Return a JSON response with the new address**
            address_response = {
                'address_id': user_address.address_id,
                'address_1': user_address.address_1,
                'address_2': user_address.address_2,
                'city': user_address.city,
                'state': user_address.state,
                'country': user_address.country,
                'pincode': user_address.pincode
            }

            # Add Warranty
            product_data = data['product']
            logger.info("Registering warranty for product")

            warranty_required_fields = ['product_id', 'product_purchased_date', 'warranty_start_date', 'warranty_end_date', 'warranty_status']
            for field in warranty_required_fields:
                if field not in product_data:
                    logger.warning(f"Missing warranty field: {field}")
                    return jsonify({"status": False, "status_code": 400, "message": f"{field} is required for warranty registration.", "data": {}}), 400

            # Parse and validate the dates
            try:
                purchase_date = datetime.strptime(product_data['product_purchased_date'], "%d-%m-%Y").date()
                warranty_start = datetime.strptime(product_data['warranty_start_date'], "%d-%m-%Y").date()
                warranty_end = datetime.strptime(product_data['warranty_end_date'], "%d-%m-%Y").date()

                logger.info(f"Validated dates: purchase_date={purchase_date}, warranty_start={warranty_start}, warranty_end={warranty_end}")
            except ValueError:
                logger.error("Invalid date format for warranty-related fields")
                return jsonify({'status': False, 'status_code': 400, 'message': 'Invalid date format', 'data': {}}), 400

            # Ensure the product ID exists
            product = db.session.query(models.ProductModel).filter_by(serial_no=product_data['product_id']).first()
            if not product:
                logger.warning(f"Product with ID {product_data['product_id']} not found")
                return jsonify({'status': False, 'status_code': 404, 'message': 'Product not found', 'data': {}}), 404
            
            # Check if a warranty already exists for this product and user
            existing_warranty = db.session.query(models.WarrantyModel).filter_by(
                customer_id=user.user_id,
                product_id=product_data['product_id']
            ).first()

            if existing_warranty:
                logger.warning(f"Duplicate warranty registration attempt for product {product_data['product_id']} and user {user.user_id}")
                return jsonify({
                    'status': False,
                    'status_code': 409,
                    'message': 'Warranty already registered for this product and user.',
                    'data': {}
                }), 409
            
            # Register new warranty
            new_warranty = models.WarrantyModel(
                customer_id=user.user_id,
                product_id=product_data['product_id'],
                product_purchased_date=purchase_date,
                warranty_start_date=warranty_start,
                warranty_period=product.warranty_period,
                warranty_end_date=warranty_end,
                warranty_status=product_data['warranty_status'],
                attachment=product_data.get('attachment', "")
            )

            db.session.add(new_warranty)
            db.session.commit()
            logger.info(f"Warranty for product {new_warranty.product_id} registered successfully")
            
            # Send a email notification to the user
            email_data = {
                "title": "Warranty Registration",
                "body": f"Your warranty for product {product.name} has been registered successfully.",
                "template": "mail/warranty.html",
                "product_name" : product.name,
                "warranty_start_date": new_warranty.warranty_start_date.strftime('%d-%m-%Y'),
                "warranty_end_date": new_warranty.warranty_end_date.strftime('%d-%m-%Y'),
                "warranty_period": new_warranty.warranty_period,
                "email": user.email,
            }
            print(email_data)
            email_sent = send_email_warranty(email_data)

            # Prepare the response data
            response_data = {
                "userData": {
                    'user_id': user.user_id,
                    'name': user.name,
                    'phone_number': user.phone_number,
                    'customer_type': user.customer_type,
                    'email': user.email
                },
                "addressData": address_response,
                "warrantyData": {
                    'product_id': new_warranty.product_id,
                    'product_purchased_date': new_warranty.product_purchased_date.strftime('%d-%m-%Y'),
                    'warranty_start_date': new_warranty.warranty_start_date.strftime('%d-%m-%Y'),
                    'warranty_end_date': new_warranty.warranty_end_date.strftime('%d-%m-%Y'),
                    'warranty_status': new_warranty.warranty_status
                }
            }

            # Return successful response
            return jsonify({
                'status': True,
                'status_code': 201,
                'message': 'Warranty registered successfully',
                'data': response_data
            }), 201

        except Exception as e:
            logger.error(f"An error occurred during warranty registration: {str(e)}")
            return jsonify({'status': False, 'status_code': 500, 'message': 'Internal Server Error', 'data': {}}), 500
