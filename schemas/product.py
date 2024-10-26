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



class ProductSchema(Schema):
    product_id = fields.Int(dump_only=True)
    name = fields.Str(required=True)
    type = fields.Str(required=True)
    model = fields.Str(required=True)
    capacity = fields.Str(required=True)
    warranty = fields.Boolean(required=True)
    warranty_period = fields.Str(required=True)
    serial_no = fields.Str(required=True)
    unique_no = fields.Str(required=True)
    date_of_manufacture = CustomDate(required=True)  # Use CustomDate for custom date format\


class ProductResponseSchema(Schema):
    product_id = fields.Int(dump_only=True)
    name = fields.Str(dump_only=True)
    type = fields.Str(dump_only=True)
    model = fields.Str(dump_only=True)
    capacity = fields.Str(dump_only=True)
    warranty = fields.Str(dump_only=True)
    warranty_period = fields.Method("get_warranty_period")  # Use custom method to format warranty period
    serial_no = fields.Str(dump_only=True)
    unique_no = fields.Str(dump_only=True)
    date_of_manufacture = fields.Method("get_date_of_manufacture")

    def get_date_of_manufacture(self, obj):
        date = obj.date_of_manufacture
        return date.strftime("%d-%m-%Y")

    # Custom method to convert days to a more readable format
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

