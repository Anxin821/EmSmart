from sqlalchemy.orm import Session

from app.models import User, UserPermission


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def list_users(db: Session):
    return db.query(User).order_by(User.id).all()


def get_user_permissions(db: Session, user_id: int):
    return db.query(UserPermission).filter(UserPermission.user_id == user_id).all()
