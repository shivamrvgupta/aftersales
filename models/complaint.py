from sqlalchemy import func
from db import db

class ComplaintModel(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.String, nullable=False)
    issue = db.Column(db.String(255), nullable=False)
    attachment = db.Column(db.String(255), nullable=True)  # Path to the invoice or attachment file
    assignee = db.Column(db.String(255), nullable=False)
    logged_by = db.Column(db.String(255), nullable=False)
    logged_at = db.Column(db.Date, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    is_major_issue = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f"<Complaint(id={self.id}, complaint_id='{self.complaint_id}', issue='{self.issue}', status='{self.status}', assignee='{self.assignee}')>"
