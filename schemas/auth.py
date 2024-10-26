from marshmallow import Schema, fields, ValidationError,validate
from datetime import datetime



class CustomDate(fields.Date):
    def __init__(self, *args, **kwargs):
        self.input_format = kwargs.pop('input_format', '%d_%m_%Y')
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        try:
            return datetime.strptime(value, self.input_format).date()
        except ValueError as e:
            raise ValidationError("Invalid date format.") from e

class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    customer_type = fields.Str(required=True)
    phone_number = fields.Str(required=True, nullable=True)
    email = fields.Email(required=False, allow_none=True)
    company_id = fields.Int(dump_only=True)
    company_name = fields.Str(required=False, allow_none=True)
    gst_number = fields.Str(required=False, allow_none=True)
    is_active = fields.Bool(required=False, missing=True)
    is_verified = fields.Bool(required=False, missing=False)
    reset_password = fields.Bool(dump_only=True)
    is_email_verified = fields.Bool(dump_only=True)

class UserResponseSchema(Schema):
    user_id = fields.Str(dump_only=True) 
    token_id = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    name = fields.Str(dump_only=True)
    customer_type = fields.Str(dump_only=True)
    phone_number = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    reset_password = fields.Bool(dump_only=True)
    is_email_verified = fields.Bool(dump_only=True)

class CompanyResponseSchema(Schema):
    company_id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    gst_number = fields.Str(dump_only=True)

class UserAddressSchema(Schema):
    address_id = fields.Int(dump_only=True) 
    address_1 = fields.Str(required=False, allow_none=True)
    address_2 = fields.Str(required=False, allow_none=True)
    city = fields.Str(required=False, allow_none=True)
    state = fields.Str(required=False, allow_none=True)
    country = fields.Str(required=False, allow_none=True)
    pincode = fields.Str(required=False, allow_none=True)

class AddressResponseSchema(Schema):
    address_id = fields.Str(dump_only=True)
    user_id = fields.Str(dump_only=True)
    address_1 = fields.Str(dump_only=True)
    address_2 = fields.Str(dump_only=True)
    city = fields.Str(dump_only=True)
    state = fields.Str(dump_only=True)
    country = fields.Str(dump_only=True)
    pincode = fields.Str(dump_only=True)

from marshmallow import Schema, fields

class PagesSchema(Schema):
    component_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)

class UserRoleSchema(Schema):
    role_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    status = fields.Bool(required=False, default=True)
    pages = fields.List(fields.Nested(PagesSchema), dump_only=True) 

class LoginSchema(Schema):
    phone_number = fields.Str(required=True, nullable=True)
    otp = fields.Str(required=False)

class LoginEmailSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=False)

class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)
    code = fields.Int(required=True)
    password = fields.Str(required=True)

class UserProfileSchema(Schema):
    user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    customer_type = fields.Str(required=True)
    email = fields.Email(required=False , allow_none=True)
    phone_number = fields.Str(required=True)

class EmailVerificationSchema(Schema):
    verification_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    verification_token = fields.Str(required=True)
    sent_at = fields.DateTime(dump_only=True)
    expires_at = fields.DateTime(required=True)
    is_verified = fields.Bool()

class PagesSchema(Schema):
    component_id = fields.Int(dump_only=True)  # For GET
    name = fields.Str(required=True, validate=validate.Length(min=1, max=50))  # Required for both GET and POST

    # Permissions fields (can_write, can_read, can_create, can_update)
    can_write = fields.Bool(required=False, missing=False)  # Default: False
    can_read = fields.Bool(required=False, missing=True)  # Default: True
    can_create = fields.Bool(required=False, missing=False)  # Default: False
    can_update = fields.Bool(required=False, missing=False)  # Default: False

    # Status field
    status = fields.Bool(required=False, missing=True)  # Default: True

class RoleSchema(Schema):
    role_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    description = fields.Str(required=False)
    status = fields.Bool(required=False)
    pages = fields.List(fields.Nested(PagesSchema), dump_only=True)  # Serialize pages



class ComplaintSchema(Schema):
    complaint_id = fields.Str(required=True, validate=validate.Length(min=1))
    issue = fields.Str(required=True, validate=validate.Length(max=255))
    attachment = fields.Str(required=False, allow_none=True)
    assignee = fields.Str(required=True, validate=validate.Length(max=255))
    logged_by = fields.Str(required=True, validate=validate.Length(max=255))
    logged_at = fields.Date(required=True, format="%d-%m-%Y")
    duration = fields.Int(required=True)
    status = fields.Str(required=True, validate=validate.OneOf(["Open", "In Progress", "Closed", "Resolved"]))
    is_major_issue = fields.Str(required=True, validate=validate.OneOf(["Yes", "No"]))


class ComplaintResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    complaint_id = fields.Str()
    issue = fields.Str()
    attachment = fields.Str(allow_none=True)
    assignee = fields.Str()
    logged_by = fields.Str()
    logged_at = fields.Date(format="%d-%m-%Y")
    duration = fields.Int()
    status = fields.Str()
    is_major_issue = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
