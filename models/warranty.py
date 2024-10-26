from sqlalchemy import func
from db import db

class WarrantyModel(db.Model):
    __tablename__ = "warranties"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(db.String, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    seller_id = db.Column(db.Integer, nullable=True)  # Assuming you will reference the seller from a different table
    product_purchased_date = db.Column(db.Date, nullable=False)
    warranty_period = db.Column(db.String(100), nullable=False)
    warranty_start_date = db.Column(db.Date, nullable=False)
    warranty_end_date = db.Column(db.Date, nullable=False)
    warranty_status = db.Column(db.String(50), nullable=False)  # Status like 'Active', 'Expired', etc.
    attachment = db.Column(db.String(255), nullable=True)  # Path to the invoice or attachment file

    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        return (
            f"Warranty(id={self.id}, product_id={self.product_id}, seller_id={self.seller_id}, "
            f"customer_id={self.customer_id}, product_purchased_date={self.product_purchased_date}, "
            f"warranty_period={self.warranty_period}, warranty_start_date={self.warranty_start_date}, "
            f"warranty_end_date={self.warranty_end_date}, warranty_status={self.warranty_status}, "
            f"attachment={self.attachment}, created_at={self.created_at}, updated_at={self.updated_at})"
        )
