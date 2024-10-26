from flask import request, jsonify
from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
from twilio.rest import Client
import models
import logging
from sqlalchemy.orm import Session
from flask_jwt_extended import jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from schemas.warranty import WarrantySchema, WarrantyResponseSchema
from schemas.product import ProductResponseSchema
from utils.service import AuthService
from utils.ai import AIService
from db import db
from datetime import datetime


client = Client(account_sid, auth_token)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bcrypt = Bcrypt()

blp = Blueprint("Warranty", "warranty", description="Operations to add and manage warranty")

@blp.route("/add-warranty")
class AddWarranty(MethodView):
    @jwt_required()
    def post(self):
        try:
            jwt = get_jwt()
            user_id = jwt.get("user_id")
            if jwt.get("role") not in ["Customer"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            # Get the customer 

            customer = models.CustomerModel.query.get(user_id)
            if not customer:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Customer not found', 'data': {}}), 400

            warranty_data = request.get_json()
            warranty_schema = WarrantySchema()
            validated_data = warranty_schema.load(warranty_data)
            print(warranty_data)
            if not validated_data:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Invalid data', 'data': {}}), 400

            # Check if warranty for the product already exists
            existing_warranty = models.WarrantyModel.query.filter_by(product_id=warranty_data['product_id']).first()
            if existing_warranty:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Warranty already exists for this product', 'data': {}}), 400

            # Parse the product purchase date
            purchased_date = datetime.strptime(warranty_data['product_purchased_date'], "%d-%m-%Y").date()

            # Check Product 
            product = models.ProductModel.query.filter_by(serial_no=warranty_data['product_id']).first()

            if not product:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Product not found', 'data': {}}), 400

            # Access the warranty period using dot notation
            warranty_period = product.warranty_period

            # Calculate warranty dates and status
            warranty_start_date, warranty_end_date, warranty_status = AuthService.calculate_warranty_dates(purchased_date, warranty_period)

            # Create new warranty
            new_warranty = models.WarrantyModel(
                product_id=warranty_data['product_id'],
                customer_id=user_id,
                product_purchased_date=purchased_date,  # Pass the date object here
                warranty_period=warranty_period,
                warranty_start_date=warranty_start_date,  # Ensure this is a date object
                warranty_end_date=warranty_end_date,  # Ensure this is a date object
                warranty_status=warranty_status,
                attachment=warranty_data.get('attachment')
            )

            db.session.add(new_warranty)
            db.session.commit()
            

            message = client.messages.create(
                from_='whatsapp:+14155238886',
                content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
                content_variables='{"1":"12/1","2":"3pm"}',
                to='whatsapp:+91' + str(customer.phone_number)
            )


            # Serialize warranty data
            warranty_schema = WarrantyResponseSchema()
            response_data = warranty_schema.dump(new_warranty)
            return jsonify({'status': True, 'status_code': 201, 'message': 'Warranty Added Successfully', 'data': response_data}), 201

        except ValidationError as ve:
            return jsonify({"status": False, "status_code": 400, "message": "Validation Error", "data": ve.messages}), 400
        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()

@blp.route("/get/<int:warranty_id>")
class GetWarrantyById(MethodView):
    @jwt_required()
    def get(self, warranty_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["Customer", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            # Fetch warranty by ID
            warranty = models.WarrantyModel.query.get(warranty_id)

            if not warranty:
                return jsonify({"status": False, "status_code": 404, "message": "Warranty Not Found", "data": {}}), 404

            product = models.ProductModel.query.filter_by(serial_no=warranty.product_id).first()

            # Serialize Product data
            product_schema = ProductResponseSchema()
            product_data = product_schema.dump(product)

            # Serialize warranty data
            warranty_schema = WarrantyResponseSchema()
            warranty_data = warranty_schema.dump(warranty)

            response_data = {
                "product": product_data,
                "warranty": warranty_data
            }

            return jsonify({"status": True, "status_code": 200, "message": "Warranty Found", "data": response_data}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()

@blp.route("/calculate-warranty-dates")
class CalculateWarrantyDates(MethodView):
    @jwt_required()
    def post(self):
        try:
            jwt = get_jwt()
            user_id = jwt.get("user_id")
            if jwt.get("role") not in ["Customer"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            data = request.get_json()
            product_id = data.get('product_id')
            purchase_date_str = data.get('product_purchased_date')

            if not product_id or not purchase_date_str:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Product ID and Purchase Date are required', 'data': {}}), 400

            # Parse the purchase date
            try:
                purchased_date = datetime.strptime(purchase_date_str, "%d-%m-%Y").date()
            except ValueError:
                return jsonify({'status': False, 'status_code': 400, 'message': 'Invalid purchase date format', 'data': {}}), 400

            # Check Product
            product = models.ProductModel.query.filter_by(serial_no=product_id).first()
            if not product:
                return jsonify({'status': False, 'status_code': 404, 'message': 'Product not found', 'data': {}}), 404

            # Access the warranty period using dot notation
            warranty_period = product.warranty_period

            # Calculate warranty dates and status
            warranty_start_date, warranty_end_date, warranty_status = AuthService.calculate_warranty_dates(purchased_date, warranty_period)

            return jsonify({
                'status': True,
                'status_code': 200,
                'message': 'Warranty Dates Calculated Successfully',
                'data': {
                    'warranty_start_date': warranty_start_date.strftime("%d-%m-%Y"),
                    'warranty_end_date': warranty_end_date.strftime("%d-%m-%Y"),
                    'warranty_status': warranty_status
                }
            }), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500

@blp.route("/get")
class GetAllWarranties(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["Customer", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            user_id = jwt.get("user_id")

            # Fetch all warranties for the customer
            warranties = models.WarrantyModel.query.filter_by(customer_id=user_id).all()

            if not warranties:
                return jsonify({"status": True, "status_code": 200, "message": "Warranties Not Found", "data": {}}), 200

            # Initialize response data
            response_data = []

            # Loop through warranties and fetch product data based on serial_no
            for warranty in warranties:
                # Fetch the product corresponding to the warranty's serial.no
                product = models.ProductModel.query.filter_by(serial_no=warranty.product_id).first()

                # If product is found, add it to the response with warranty data
                warranty_data = WarrantyResponseSchema().dump(warranty)
                product_data = ProductResponseSchema().dump(product) if product else {}

                # Append combined warranty and product data to response
                response_data.append({
                    "warranty": warranty_data,
                    "product": product_data
                })

            return jsonify({"status": True, "status_code": 200, "message": "Warranties Retrieved Successfully", "data": response_data}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()



@blp.route("/get-repair-cost-ai", methods=["POST"])
class GetRepairCostAI(MethodView):
    @jwt_required()
    def post(self):
        try:
            # Extract the JSON body from the request
            data = request.get_json()

            if not data or "fault_description" not in data:
                return jsonify({"status": False, "status_code": 400, "message": "Missing fault description", "data": {}}), 400

            fault_description = data["fault_description"]

            # Use the AI Service to estimate the repair cost
            ai_service = AIService()
            estimated_cost = ai_service.estimate_cost(fault_description)

            if estimated_cost is None:
                return jsonify({"status": False, "status_code": 500, "message": "AI Service Error", "data": {}}), 500

            return jsonify({
                "status": True,
                "status_code": 200,
                "message": "Repair cost estimated successfully",
                "data": estimated_cost
            }), 200

        except Exception as e:
            return jsonify({
                "status": False,
                "status_code": 500,
                "message": "Internal Server Error",
                "data": {"error": str(e)}
            }), 500