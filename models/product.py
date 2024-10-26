from sqlalchemy import func
from db import db

class ProductModel(db.Model):
    __tablename__ = "products"

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.String(100), nullable=False)
    warranty = db.Column(db.Boolean, default=True)
    warranty_period = db.Column(db.String(100), nullable=False)
    serial_no = db.Column(db.String(100), nullable=False)
    unique_no = db.Column(db.String(100), nullable=False)
    date_of_manufacture = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        return (
            f"Product(product_id={self.product_id}, name={self.name}, "
            f"type={self.type}, model={self.model}, capacity={self.capacity}, "
            f"warranty={self.warranty}, warranty_period={self.warranty_period}, "
            f"serial_no={self.serial_no}, unique_no={self.unique_no}, "
            f"date_of_manufacture={self.date_of_manufacture}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )
