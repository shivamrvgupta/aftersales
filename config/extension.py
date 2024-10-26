from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_cors import CORS
from db import db

migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def init_extensions(app):
    CORS(app, resource={r"/*": {"origins": "*"}})
    db.init_app(app)    
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

