from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.role import Role

def seed_roles():
    db: Session = SessionLocal()
    roles = ["Admin", "Author", "Reader"]
    for role_name in roles:
        if not db.query(Role).filter_by(name=role_name).first():
            db.add(Role(name=role_name))
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_roles()
"""
Script to seed default roles into the roles table.
Run this after your first migration and before registering users:
    poetry run python -m app.db.seed_roles
"""

