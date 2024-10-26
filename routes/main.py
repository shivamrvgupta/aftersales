from flask import Blueprint
from flask_smorest import Api
from resources.customer.users import blp as UsersBlueprint
from resources.customer.roles import blp as RolesBlueprint
from resources.customer.auth import blp as AuthBlueprint
from resources.customer.product import blp as ProductBlueprint
from resources.customer.health import blp as HealthBlueprint
from resources.customer.authentication import blp as AuthenticationBlueprint
from resources.customer.general import blp as GeneralBlueprint
from resources.customer.warranty import blp as WarrantyBlueprint
from resources.customer.complaint import blp as ComplaintBlueprint


from resources.admin.auth import blp as AdminAuthBlueprint
from resources.admin.users import blp as AdminUsersBlueprint
from resources.admin.role import blp as AdminRolesBlueprint
from resources.admin.product import blp as AdminProductBlueprint
from resources.admin.warranty import blp as AdminWarrantyBlueprint
from resources.admin.pages import blp as AdminPagesBlueprint

def register_blueprints(app):
    api = Api(app)
    api.register_blueprint(HealthBlueprint, url_prefix="/api/v1/")
    api.register_blueprint(UsersBlueprint, url_prefix="/api/v1/customer")
    api.register_blueprint(RolesBlueprint, url_prefix="/api/v1/auth/roles")
    api.register_blueprint(AuthBlueprint, url_prefix="/api/v1/auth/email")
    api.register_blueprint(ProductBlueprint, url_prefix="/api/v1/product")
    api.register_blueprint(AuthenticationBlueprint, url_prefix="/api/v1/auth")
    api.register_blueprint(GeneralBlueprint, url_prefix="/api/v1/general")
    api.register_blueprint(ComplaintBlueprint, url_prefix="/api/v1/complaint")
    api.register_blueprint(WarrantyBlueprint, url_prefix="/api/v1/warranty")

    api.register_blueprint(AdminAuthBlueprint, url_prefix="/api/v1/admin/auth")
    api.register_blueprint(AdminUsersBlueprint, url_prefix="/api/v1/admin/users")
    api.register_blueprint(AdminRolesBlueprint, url_prefix="/api/v1/admin/roles")
    api.register_blueprint(AdminProductBlueprint, url_prefix="/api/v1/admin/product")
    api.register_blueprint(AdminWarrantyBlueprint, url_prefix="/api/v1/admin/warranty")
    api.register_blueprint(AdminPagesBlueprint, url_prefix="/api/v1/admin/pages")