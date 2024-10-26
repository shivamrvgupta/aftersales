from sqlalchemy import func
from db import db

class SellerModel(db.Model):
    __tablename__ = "sellers"

    seller_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    business_name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    gst_number = db.Column(db.String(100), nullable=True)
    mobile_primary = db.Column(db.String(20), nullable=False)
    mobile_secondary = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    area = db.Column(db.Text, nullable=False)
    locality = db.Column(db.Text, nullable=False)
    city = db.Column(db.Text, nullable=False)
    state = db.Column(db.Text, nullable=False)
    country = db.Column(db.Text, nullable=False)
    pincode = db.Column(db.String(50), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_email = db.Column(db.String(100), nullable=False)
    owner_mobile_primary = db.Column(db.String(20), nullable=False)
    owner_mobile_secondary = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        # Return All
        return (
            f"Seller(seller_id={self.seller_id}, business_name={self.business_name}, "
            f"type={self.type}, gst_number={self.gst_number}, mobile_primary={self.mobile_primary}, "
            f"mobile_secondary={self.mobile_secondary}, email={self.email}, address={self.address}, "
            f"area={self.area}, locality={self.locality}, city={self.city}, state={self.state}, "
            f"country={self.country}, pincode={self.pincode}, owner_name={self.owner_name}, "
            f"owner_email={self.owner_email}, owner_mobile_primary={self.owner_mobile_primary}, "
            f"owner_mobile_secondary={self.owner_mobile_secondary}, created_at={self.created_at}, "
            f"updated_at={self.updated_at})"
        )