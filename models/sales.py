from sqlalchemy import func
from db import db

class SalesModel(db.Model):
    __tablename__ = "sales"

    sales_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date_of_purchased = db.Column(db.Date, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.seller_id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    attachment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)    

    # Define the relationship to ProductModel and SellerModel
    product = db.relationship("ProductModel", backref="sales")
    seller = db.relationship("SellerModel", backref="sales")

    def __repr__(self):
        return (
            f"Sales(sales_id={self.sales_id}, date_of_purchased={self.date_of_purchased}, "
            f"quantity={self.quantity}, product_id={self.product_id}, seller_id={self.seller_id}, "
            f"customer_id={self.customer_id}, attachment={self.attachment}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )
