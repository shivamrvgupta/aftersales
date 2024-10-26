
from marshmallow import Schema, fields, ValidationError
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
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)
    confirm_password = fields.Str(required=True, load_only=True)
    phone_number = fields.Str(required=False, allow_none=True)
    company_name = fields.Str(required=False, allow_none=True)
    gst_number = fields.Str(required=False, allow_none=True)
    is_active = fields.Bool(required=False, missing=True)
    is_verified = fields.Bool(required=False, missing=False)
    address_id = fields.Int(dump_only=True) 
    address_1 = fields.Str(required=False, allow_none=True)
    address_2 = fields.Str(required=False, allow_none=True)
    city = fields.Str(required=False, allow_none=True)
    state = fields.Str(required=False, allow_none=True)
    country = fields.Str(required=False, allow_none=True)
    pincode = fields.Str(required=False, allow_none=True)

class UserResponseSchema(Schema):
    user_id = fields.Str(dump_only=True) 
    token_id = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    name = fields.Str(dump_only=True)
    customer_type = fields.Str(dump_only=True)
    phone_number = fields.Str(dump_only=True)
    gst_number = fields.Str(dump_only=True)
    is_active = fields.Bool(dump_only=True)
    is_verified = fields.Bool(dump_only=True)
    reset_password = fields.Bool(dump_only=True)
    is_email_verified = fields.Bool(dump_only=True)

class UserAddressSchema(Schema):
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

class CompanyResponseSchema(Schema):
    company_id = fields.Str(dump_only=True)
    name = fields.Str(dump_only=True)
    gst_number = fields.Str(dump_only=True)

class UserRoleSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(required=True)

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class PasswordResetRequestSchema(Schema):
    reset_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    reset_token = fields.Str(required=True)
    requested_at = fields.DateTime(dump_only=True)
    expires_at = fields.DateTime(required=True)
    is_used = fields.Bool()


class ForgotPasswordSchema(Schema):
    email = fields.Email(required=True)
    code = fields.Int(required=True)
    password = fields.Str(required=True)

class ResetPasswordSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
    confirm_password = fields.Str(required=True, load_only=True)

class UserProfileSchema(Schema):
    user_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    customer_type = fields.Str(required=True)
    email = fields.Email(required=True)
    phone_number = fields.Str(required=True, allow_none=True)
    gst_number = fields.Str(required=True, allow_none=True)


class EmailVerificationSchema(Schema):
    verification_id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    verification_token = fields.Str(required=True)
    sent_at = fields.DateTime(dump_only=True)
    expires_at = fields.DateTime(required=True)
    is_verified = fields.Bool()