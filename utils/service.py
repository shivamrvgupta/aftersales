from werkzeug.security import generate_password_hash, check_password_hash
import jwt, re , random , secrets, string , os
from datetime import datetime, timedelta
from flask import current_app
from dotenv import load_dotenv

load_dotenv()

class AuthService:
    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    @staticmethod
    def check_password(hash, password):
        return check_password_hash(hash, password)

    @staticmethod
    def generate_token(user_id):
        # Make the id to String
        return jwt.encode({'user_id': user_id}, os.getenv('JWT_SECRET_KEY') , algorithm='HS256')

    @staticmethod
    def decode_token(token):
        try:
            payload = jwt.decode(token, current_app.config.get('JWT_SECRET_KEY'), algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Token expired. Please log in again.'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please log in again.'
    
    @staticmethod
    def generate_4_digit_code():
        return random.randint(1000, 9999)
    
    @staticmethod
    def generate_random_mixed_token(length=32):
        """Generate a random mixed token with letters, digits, and special characters."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length)) 
    
    @staticmethod
    def normalize_phone_number(phone_number):
        # Remove any non-numeric characters
        normalized_number = re.sub(r'\D', '', phone_number)
        
        # Check if the phone number has a country code, trim to last 10 digits
        if len(normalized_number) > 10:
            normalized_number = normalized_number[-10:]

        return normalized_number

    @staticmethod
    def calculate_warranty_dates(purchased_date, warranty_period_str):
        # Convert the warranty period to an integer (assuming it's passed as days)
        warranty_period_days = int(warranty_period_str)
        
        # Warranty starts on the product purchase date
        warranty_start_date = purchased_date
        
        # Warranty ends by adding warranty period in days to the start date
        warranty_end_date = warranty_start_date + timedelta(days=warranty_period_days)
        
        # Determine the warranty status (Active or Expired)
        current_date = datetime.now().date()
        warranty_status = "Active" if current_date <= warranty_end_date else "Expired"
        
        return warranty_start_date, warranty_end_date, warranty_status