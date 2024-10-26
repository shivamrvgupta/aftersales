from marshmallow import Schema, fields, ValidationError
from datetime import datetime

class CustomDate(fields.Date):
    def __init__(self, *args, **kwargs):
        self.input_format = kwargs.pop('input_format', '%d-%m-%Y')
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        try:
            return datetime.strptime(value, self.input_format).date()
        except ValueError as e:
            raise ValidationError("Invalid date format.") from e

class WarrantySchema(Schema):
    product_id = fields.Str(required=True) 
    product_purchased_date = CustomDate(required=True)
    attachment = fields.Str()
    warranty_end_date = CustomDate(required=True)
    warranty_start_date = CustomDate(required=True)
    warranty_status = fields.Bool(required=True)

class WarrantyAdminSchema(Schema):
    customer_id = fields.Int(required=True)
    product_id = fields.Str(required=True) 
    product_purchased_date = CustomDate(required=True)
    attachment = fields.Str()
    warranty_end_date = CustomDate(required=True)
    warranty_start_date = CustomDate(required=True)
    warranty_status = fields.Bool(required=True)


class WarrantyResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    customer_id = fields.Int(dump_only=True)
    product_id = fields.Str(dump_only=True)
    seller_id = fields.Int(dump_only=True)
    customer_id = fields.Int(dump_only=True)
    
    # Custom date format for product_purchased_date
    product_purchased_date = fields.Method("format_purchased_date")
    warranty_start_date = fields.Method("format_start_date")
    warranty_end_date = fields.Method("format_end_date")
    
    warranty_period = fields.Method("get_warranty_period")
    warranty_status = fields.Str(dump_only=True)
    attachment = fields.Str(dump_only=True)
    
    def get_warranty_period(self, obj):
        try:
            days = int(obj.warranty_period)  # Ensure warranty_period is an integer
        except ValueError:
            return "Invalid warranty period"  # Handle non-numeric warranty_period gracefully
        
        if days < 30:
            return f"{days} day{'s' if days > 1 else ''}"
        elif 30 <= days < 365:
            months = days // 30
            remaining_days = days % 30
            if remaining_days > 0:
                return f"{months} month{'s' if months > 1 else ''} {remaining_days} day{'s' if remaining_days > 1 else ''}"
            else:
                return f"{months} month{'s' if months > 1 else ''}"
        else:
            years = days // 365
            remaining_days = days % 365
            months = remaining_days // 30
            remaining_days = remaining_days % 30
            if months > 0 and remaining_days > 0:
                return f"{years} year{'s' if years > 1 else ''} {months} month{'s' if months > 1 else ''} {remaining_days} day{'s' if remaining_days > 1 else ''}"
            elif months > 0:
                return f"{years} year{'s' if years > 1 else ''} {months} month{'s' if months > 1 else ''}"
            elif remaining_days > 0:
                return f"{years} year{'s' if years > 1 else ''} {remaining_days} day{'s' if remaining_days > 1 else ''}"
            else:
                return f"{years} year{'s' if years > 1 else ''}"


    # Method to format dates
    def format_purchased_date(self, obj):
        return obj.product_purchased_date.strftime('%d-%m-%Y')

    def format_start_date(self, obj):
        return obj.warranty_start_date.strftime('%d-%m-%Y')

    def format_end_date(self, obj):
        return obj.warranty_end_date.strftime('%d-%m-%Y')