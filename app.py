from flask import Flask
import os
from config.config import config_dict
from config.extension import init_extensions
from config.logging_config import setup_logging
from config.error_handler import register_error_handlers
from config.jwt_handler import jwt_setup
from routes import main
from flask_mail import Mail
import pandas as pd
from db import db

# Initialize Flask App
app = Flask(__name__)
data = pd.read_csv('./utils/repair_costs_samples.csv')

# Choose Configuration based on Environment
config_mode = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config_dict[config_mode])
app.secret_key = os.getenv('JWT_SECRET_KEY', 'c8023db27990443583f10be3195a953a03bf327259782551089c70d9d018eda809bc1a8feefdabb1b9421ad2487538438d86df151f3e8b4835bbc0ac3d2217ea')
# Initialize Extensions
init_extensions(app)

with app.app_context():
    db.create_all()  # This creates all tables defined in your models


mail = Mail(app)

# Setup Logging
setup_logging(app)

jwt_setup(app)

# Register Error Handlers
register_error_handlers(app)

# Register Blueprints
main.register_blueprints(app)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6456, debug=False, use_reloader=True)

