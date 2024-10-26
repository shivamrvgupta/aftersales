from sqlalchemy import Table, Column, Integer, ForeignKey ,String , Boolean
from db import db

# Association table to connect roles and pages (components)
role_page_access = Table(
    'role_page_access',
    db.Model.metadata,
    db.Column('role_id', db.Integer, db.ForeignKey('user_roles.role_id'), primary_key=True),
    db.Column('component_id', db.Integer, db.ForeignKey('components.component_id'), primary_key=True)
)

class UserRoleModel(db.Model):
    __tablename__ = "user_roles"

    role_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.Boolean, default=True, nullable=False)

    # Many-to-many relationship with PagesModel
    pages = db.relationship('PagesModel', secondary='role_page_access', backref='roles')

    def __repr__(self):
        return f"UserRole(role_id={self.role_id}, name={self.name}, description={self.description})"


class PagesModel(db.Model):
    __tablename__ = "components"

    component_id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(50), unique=True, nullable=False)
    status = db.Column(Boolean, default=True, nullable=False)

    # Permission fields
    can_write = db.Column(Boolean, default=False, nullable=False)
    can_read = db.Column(Boolean, default=True, nullable=False)
    can_create = db.Column(Boolean, default=False, nullable=False)
    can_update = db.Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return (f"PagesModel(component_id={self.component_id}, name={self.name}, "
                f"can_write={self.can_write}, can_read={self.can_read}, "
                f"can_create={self.can_create}, can_update={self.can_update})")