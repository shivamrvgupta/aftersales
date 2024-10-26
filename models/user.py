from sqlalchemy import func
from db import db

class UserModel(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_type = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    reset_password = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    role_assignment = db.relationship("UserRoleAssignmentsModel", back_populates="user")
    address_assignment = db.relationship("UserAddressModel", back_populates="user")
    company_assginment = db.relationship("CompanyModel", back_populates="user")
    

    def __repr__(self):
        return (
            f"User(user_id={self.user_id}, email={self.email}, "
            f"name={self.name}, is_active={self.is_active}, "
            f"is_verified={self.is_verified}"
            f"customer_type={self.customer_type})"
        )

class CompanyModel(db.Model):
    __tablename__ = "company"

    company_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    gst_number = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    user = db.relationship("UserModel", back_populates="company_assginment")


class UserAddressModel(db.Model):
    __tablename__ = 'address'
    
    address_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    address_1 = db.Column(db.Text, nullable=True)
    address_2 = db.Column(db.Text, nullable=True)
    city = db.Column(db.Text, nullable=True)
    state = db.Column(db.Text, nullable=True)
    country = db.Column(db.Text, nullable=True)
    pincode = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    user = db.relationship("UserModel", back_populates="address_assignment")

    def __repr__(self):
        return f"UserAddress(user_id={self.user_id}, address_1={self.address_1}, address_2={self.address_2}, city={self.city}, state={self.state}, country={self.country}, pincode={self.pincode})"

class UserRoleAssignmentsModel(db.Model):
    __tablename__ = "user_role_assignments"

    user_role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('user_roles.role_id'), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    
    # Correcting the relationship back to UserModel
    user = db.relationship("UserModel", back_populates="role_assignment")
    role = db.relationship("UserRoleModel", backref="user_assignments")

    def __repr__(self):
        return f"UserRoleAssignments(user_role_id={self.user_role_id}, user_id={self.user_id}, role_id={self.role_id})"

class PasswordResetRequest(db.Model):
    __tablename__ = 'password_reset_requests'
    
    reset_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    reset_token = db.Column(db.String(255), nullable=False)
    reset_code = db.Column(db.Integer, nullable=False)
    requested_at = db.Column(db.DateTime, default=func.current_timestamp())
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f"PasswordRequests(reset_id={self.reset_id}, user_id={self.user_id}, reset_token={self.reset_token}, reset_code={self.reset_code}, requested_at={self.requested_at}, expires_at={self.expires_at}, is_used={self.is_used})"

class EmailVerification(db.Model):
    __tablename__ = 'email_verifications'
    
    verification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    verification_code = db.Column(db.Integer, nullable=False, unique=True) 
    verification_token = db.Column(db.String(255), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)
    
    def __repr__(self):
        return f"EmailVerification(verification_id={self.verification_id}, user_id={self.user_id}, verification_code={self.verification_code}, verification_token={self.verification_token}, sent_at={self.sent_at}, expires_at={self.expires_at}, is_verified={self.is_verified})"

class OtpVerification(db.Model):
    __tablename__ = 'otp_verifications'

    otp_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone_number = db.Column(db.String(50), nullable=False)
    otp = db.Column(db.Integer, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), nullable=False)
    updated_at = db.Column(db.TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=False)

    def __repr__(self):
        return f"OtpVerification(otp_id={self.otp_id}, phone={self.phone_number}, otp={self.otp}, sent_at={self.sent_at}, expires_at={self.expires_at})"
    
