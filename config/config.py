# config.py
import os
from datetime import timedelta
import logging

class Config:
    # General Configurations
    API_TITLE = "Stores REST API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    PROPAGATE_EXCEPTIONS = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_HEADERS = 'Content-Type'
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_MAX_EMAILS = None
    # JWT Configurations
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_secret_key")

    # Database Configurations
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.db")

    # Mail Configurations
    MAIL_USERNAME = "shivamrvgupta@gmail.com"
    MAIL_PASSWORD = "wbnqpfevdytkstsn"
    MAIL_DEFAULT_SENDER = 'Warranty Manager <admin@warrantymanager.com>'

    # Logging Configurations
    LOG_FILENAME = 'logs/app.log'
    LOG_LEVEL = logging.ERROR

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///warrantyManager.db"

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///warrantyManager.db"

config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}
