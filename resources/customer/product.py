from flask import request, jsonify
from flask_restful import Resource
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
from models import ProductModel , WarrantyModel
from sqlalchemy.orm import Session
from flask_jwt_extended import jwt_required, get_jwt
from flask_bcrypt import Bcrypt
from schemas.product import ProductSchema , ProductResponseSchema
from db import db
from datetime import datetime

bcrypt = Bcrypt()

blp = Blueprint("Products", "products", description="Operations to check manage products")

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
            query = db.session.query(ProductModel)

            # Apply filters based on the parameters provided
            if name:
                query = query.filter(ProductModel.name.like(f"%{name}%"))
            if serial_no:
                query = query.filter(ProductModel.serial_no.like(f"%{serial_no}%"))
            if model:
                query = query.filter(ProductModel.model.like(f"%{model}%"))
            if unique_no:
                query = query.filter(ProductModel.unique_no.like(f"%{unique_no}%"))

            # Fetch the results
            products = query.all()
            
            if not products:
                return {"status": False, "status_code": 404, "message": "No products found", "data": {}}, 404

            # Check if warranty is already registered and if product has warranty support
            for product in products:
                warranty = db.session.query(WarrantyModel).filter(WarrantyModel.product_id == product.serial_no).first()
                
                if warranty:
                    return {"status": False, "status_code": 409, "message": f"Warranty already exists for product {product.serial_no}", "data": {}}, 409

                # Check if the product provides warranty support using the 'warranty' field
                if not product.warranty:
                    return {"status": True, "status_code": 200, "message": f"Product {product.serial_no} does not provide warranty support", "data": {}}, 200

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

            
@blp.route("/all-products")
class AllProducts(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()

            if not jwt:
                return {"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}, 401
            
            # Query the products
            products = db.session.query(ProductModel).all()
            
            if not products:
                return {"status": False, "status_code": 404, "message": "Product not found", "data": []}, 404
            
            # Serialize the products
            schema = ProductResponseSchema(many=True)
            productData = schema.dump(products)

            return {"status": True, "status_code": 200, "message": "Product found", "data": productData}

        except Exception as e:
            return {"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}, 500

        finally:
            db.session.close()

