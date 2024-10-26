from flask import request, jsonify
from datetime import datetime
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from marshmallow import ValidationError
import models
import logging
from flask_jwt_extended import jwt_required, get_jwt
from db import db
from schemas.auth import ComplaintSchema, ComplaintResponseSchema

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

blp = Blueprint("Complaint", "complaint", description="Operations to add and manage complaints")

# Endpoint to add a new complaint
@blp.route("/add-complaint")
class AddComplaint(MethodView):
    @jwt_required()
    def post(self):
        try:
            jwt = get_jwt()
            user_id = jwt.get("user_id")

            # Only 'Customer' can add complaints
            if jwt.get("role") not in ["Customer"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            complaint_data = request.get_json()
            complaint_schema = ComplaintSchema()
            validated_data = complaint_schema.load(complaint_data)

            # Check if complaint ID already exists
            existing_complaint = models.ComplaintModel.query.filter_by(complaint_id=validated_data['complaint_id']).first()
            if existing_complaint:
                return jsonify({"status": False, "status_code": 400, "message": "Complaint ID already exists", "data": {}}), 400

            # Create a new complaint
            new_complaint = models.ComplaintModel(
                complaint_id=validated_data['complaint_id'],
                issue=validated_data['issue'],
                attachment=validated_data.get('attachment'),
                assignee=validated_data['assignee'],
                logged_by=user_id,
                logged_at=datetime.strptime(validated_data['logged_at'], "%d-%m-%Y").date(),
                duration=validated_data['duration'],
                status=validated_data['status'],
                is_major_issue=validated_data['is_major_issue']
            )

            db.session.add(new_complaint)
            db.session.commit()

            # Serialize and return the complaint data
            response_data = ComplaintResponseSchema().dump(new_complaint)
            return jsonify({"status": True, "status_code": 201, "message": "Complaint Added Successfully", "data": response_data}), 201

        except ValidationError as ve:
            return jsonify({"status": False, "status_code": 400, "message": "Validation Error", "data": ve.messages}), 400
        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()


# Endpoint to retrieve a single complaint by ID
@blp.route("/get/<int:complaint_id>")
class GetComplaintById(MethodView):
    @jwt_required()
    def get(self, complaint_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["Customer", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            complaint = models.ComplaintModel.query.get(complaint_id)
            if not complaint:
                return jsonify({"status": False, "status_code": 404, "message": "Complaint Not Found", "data": {}}), 404

            response_data = ComplaintResponseSchema().dump(complaint)
            return jsonify({"status": True, "status_code": 200, "message": "Complaint Found", "data": response_data}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()


# Endpoint to retrieve all complaints for a customer
@blp.route("/get")
class GetAllComplaints(MethodView):
    @jwt_required()
    def get(self):
        try:
            jwt = get_jwt()
            user_id = jwt.get("user_id")

            # Only 'Customer' and 'Admin' can access all complaints
            if jwt.get("role") not in ["Customer", "Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            complaints = models.ComplaintModel.query.filter_by(logged_by=user_id).all()
            if not complaints:
                return jsonify({"status": True, "status_code": 200, "message": "No Complaints Found", "data": {}}), 200

            response_data = ComplaintResponseSchema(many=True).dump(complaints)
            return jsonify({"status": True, "status_code": 200, "message": "Complaints Retrieved Successfully", "data": response_data}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()


# Endpoint to update a complaint by ID
@blp.route("/update/<int:complaint_id>")
class UpdateComplaint(MethodView):
    @jwt_required()
    def put(self, complaint_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            complaint = models.ComplaintModel.query.get(complaint_id)
            if not complaint:
                return jsonify({"status": False, "status_code": 404, "message": "Complaint Not Found", "data": {}}), 404

            complaint_data = request.get_json()
            for key, value in complaint_data.items():
                setattr(complaint, key, value)

            db.session.commit()
            response_data = ComplaintResponseSchema().dump(complaint)
            return jsonify({"status": True, "status_code": 200, "message": "Complaint Updated Successfully", "data": response_data}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()


# Endpoint to delete a complaint by ID
@blp.route("/delete/<int:complaint_id>")
class DeleteComplaint(MethodView):
    @jwt_required()
    def delete(self, complaint_id):
        try:
            jwt = get_jwt()
            if jwt.get("role") not in ["Admin"]:
                return jsonify({"status": False, "status_code": 401, "message": "Unauthorized Access", "data": {}}), 401

            complaint = models.ComplaintModel.query.get(complaint_id)
            if not complaint:
                return jsonify({"status": False, "status_code": 404, "message": "Complaint Not Found", "data": {}}), 404

            db.session.delete(complaint)
            db.session.commit()
            return jsonify({"status": True, "status_code": 200, "message": "Complaint Deleted Successfully", "data": {}}), 200

        except Exception as e:
            return jsonify({"status": False, "status_code": 500, "message": "Internal Server Error", "data": {"error": str(e)}}), 500
        finally:
            db.session.close()
