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
from schemas.product import ProductSchema , ProductResponseSchema
from db import db
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bcrypt = Bcrypt()

blp = Blueprint("AdminProducts", "adminproducts", description="Operations to add and update products")


@blp.route("/search")
class SearchProduct(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()

            if not jwt: 
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
            
            # Get query parameters
            name = request.args.get("name")
            serial_no = request.args.get("serial_no")
            model = request.args.get("model")
            unique_no = request.args.get("unique_no")

            # Start query for filtering
            query = db.session.query(models.ProductModel)

            # Apply filters based on the parameters provided
            if name:
                query = query.filter(models.ProductModel.name.like(f"%{name}%"))
            if serial_no:
                query = query.filter(models.ProductModel.serial_no.like(f"%{serial_no}%"))
            if model:
                query = query.filter(models.ProductModel.model.like(f"%{model}%"))
            if unique_no:
                query = query.filter(models.ProductModel.unique_no.like(f"%{unique_no}%"))

            # Fetch the results
            products = query.all()
            
            if not products:
                return {"status": False, "status_code": 404, "message": "No products found", "data": {}}, 404

            # Serialize the products
            schema = ProductResponseSchema(many=True)
            productData = schema.dump(products)

            # Print serialized product data for debugging
            print(productData)

            return {"status": True, "status_code": 200, "message": "Products found", "data": productData}
        
        except Exception as e:
            return {"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}, 500
        
        finally:
            db.session.close()

@blp.route("/add-product")
class AddProduct(MethodView):
    @jwt_required()
    def post(self):
        try:
            jwt = get_jwt()
            print(jwt.get("role"))
            if not jwt.get("role") == "SuperAdmin" or jwt.get("role") == "Admin":
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            product_data = request.get_json()
            product_schema = ProductSchema()
            validated_data = product_schema.load(product_data)


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
            
            reponseSchema = ProductResponseSchema()
            response_data = reponseSchema.dump(new_product)


            return jsonify({'status': True, 'status_code': 201, 'message': 'Product Added Successfully', 'data': response_data}), 201
        
                
        except Exception as e:
            return {"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}, 500
        
        finally:
            db.session.close()

@blp.route("/update/<int:product_id>")
class UpdateProduct(MethodView):
    @jwt_required()
    def put(self, product_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["SuperAdmin", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            product_data = request.get_json()
            product_schema = ProductSchema()
            validated_data = product_schema.load(product_data)

            # Fetch the existing product by ID
            product = models.ProductModel.query.get(product_id)
            if not product:
                return jsonify({"status": False, "status_code": 404, "message": "Product not found", "data": {}}), 404

            # Update product with new data
            for key, value in validated_data.items():
                setattr(product, key, value)
            db.session.commit()

            response_data = product_schema.dump(product)
            return jsonify({'status': True, 'status_code': 200, 'message': 'Product updated successfully', 'data': response_data}), 200

        except Exception as e:
            logger.error(f"Error while updating product: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        
        finally:
            db.session.close()


@blp.route("/get/<int:product_id>")
@blp.route("/get-all")
class GetProduct(MethodView):
    @jwt_required()
    def get(self, product_id=None):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["SuperAdmin", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            product_schema = ProductResponseSchema()
            if product_id:
                # Fetch single product
                product = models.ProductModel.query.get(product_id)
                if not product:
                    return jsonify({"status": False, "status_code": 404, "message": "Product not found", "data": {}}), 404
                response_data = product_schema.dump(product)
                return jsonify({'status': True, 'status_code': 200, 'message': 'Product retrieved successfully', 'data': response_data}), 200
            else:
                # Fetch all products
                products = models.ProductModel.query.all()
                response_data = product_schema.dump(products, many=True)
                return jsonify({'status': True, 'status_code': 200, 'message': 'Products retrieved successfully', 'data': response_data}), 200

        except Exception as e:
            logger.error(f"Error while fetching products: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500

@blp.route("/delete/<int:product_id>")
class DeleteProduct(MethodView):
    @jwt_required()
    def delete(self, product_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["SuperAdmin", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            product = models.ProductModel.query.get(product_id)
            if not product:
                return jsonify({"status": False, "status_code": 404, "message": "Product not found", "data": {}}), 404

            db.session.delete(product)
            db.session.commit()
            return jsonify({'status': True, 'status_code': 200, 'message': 'Product deleted successfully', 'data': {}}), 200

        except Exception as e:
            logger.error(f"Error while deleting product: {str(e)}")
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        
        finally:
            db.session.close()
