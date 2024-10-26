from flask.views import MethodView
from flask_smorest import Blueprint, abort
from schemas.auth import PagesSchema
from marshmallow import ValidationError
from models import PagesModel
from flask_jwt_extended import jwt_required, get_jwt
from flask import request, jsonify
from db import db

blp = Blueprint("Pages", "pages", url_prefix="/api/v1/admin", description="Operations for managing Pages")

# Helper function to verify roles
def check_role(roles):
    jwt = get_jwt()
    if jwt.get("role") not in roles:
        abort(401, message="Unauthorized Access")

# Standardized error response function
def error_response(status_code, message, data):
    return jsonify({
        "status": False,
        "status_code": status_code,
        "message": message,
        "data": data
        # "error": str(error) if error else None
    }), status_code

# GET all pages
@blp.route("/all-pages", methods=["GET"])
class GetAllPages(MethodView):
    @jwt_required()
    def get(self):
        try:
            pages = PagesModel.query.all()
            if not pages:
                return error_response(404, "No pages found", [])

            pages_schema = PagesSchema(many=True)
            result = pages_schema.dump(pages)

            return jsonify({
                "status": True,
                "status_code": 200,
                "data": result
            }), 200
        except Exception as err:
            return error_response(500, "An error occurred", err)

# POST (Create a new page)
@blp.route("/add-pages", methods=["POST"])
class AddPage(MethodView):
    @jwt_required()
    def post(self):
        try:
            check_role(["SuperAdmin", "Admin"])

            schema = PagesSchema()
            data = schema.load(request.get_json())

            if PagesModel.query.filter_by(name=data['name']).first():
                return error_response(409, "Page with this name already exists")

            new_page = PagesModel(
                name=data['name'],
                can_write=data.get('can_write', False),
                can_read=data.get('can_read', True),
                can_create=data.get('can_create', False),
                can_update=data.get('can_update', False),
                status=data.get('status', True)
            )
            db.session.add(new_page)
            db.session.commit()

            responseData = {
                "name" : new_page.name,
                "can_write" : new_page.can_write,
                "can_read" : new_page.can_read,
                "can_create" : new_page.can_create,
                "can_update" : new_page.can_update,
                "status" : new_page.status
            }

            return jsonify({
                "status": True,
                "status_code": 201,
                "message": "Page added successfully",
                "data" : responseData
            }), 201

        except ValidationError as err:
            return error_response(400, "Validation error", err.messages)
        except Exception as err:
            return error_response(500, "An error occurred", err)

# PUT (Update an existing page)
@blp.route("/update-pages/<int:page_id>", methods=["PUT"])
class UpdatePage(MethodView):
    @jwt_required()
    def put(self, page_id):
        try:
            check_role(["SuperAdmin", "Admin"])

            page = PagesModel.query.get(page_id)
            if not page:
                return error_response(404, "Page not found")

            schema = PagesSchema(partial=True)
            data = schema.load(request.get_json())

            page.name = data.get('name', page.name)
            page.can_write = data.get('can_write', page.can_write)
            page.can_read = data.get('can_read', page.can_read)
            page.can_create = data.get('can_create', page.can_create)
            page.can_update = data.get('can_update', page.can_update)
            page.status = data.get('status', page.status)

            db.session.commit()

            return jsonify({
                "status": True,
                "status_code": 200,
                "message": "Page updated successfully"
            }), 200

        except ValidationError as err:
            return error_response(400, "Validation error", err.messages)
        except Exception as err:
            return error_response(500, "An error occurred", err)

# DELETE (Remove a page)
@blp.route("/delete-pages/<int:page_id>", methods=["DELETE"])
class DeletePage(MethodView):
    @jwt_required()
    def delete(self, page_id):
        try:
            check_role(["SuperAdmin", "Admin"])

            page = PagesModel.query.get(page_id)
            if not page:
                return error_response(404, "Page not found")

            db.session.delete(page)
            db.session.commit()

            return jsonify({
                "status": True,
                "status_code": 200,
                "message": "Page deleted successfully"
            }), 200

        except Exception as err:
            return error_response(500, "An error occurred", err)
