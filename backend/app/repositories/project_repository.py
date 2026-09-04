from sqlalchemy.orm import Session

from app.models import Project


def get_projects(db: Session, include_inactive: bool = False):
    query = db.query(Project)
    if not include_inactive:
        query = query.filter(Project.is_active == True)
    return query.order_by(Project.project_code.asc()).all()


def get_project_by_id(db: Session, project_id: int):
    return db.query(Project).filter(Project.id == project_id).first()


def create_project(db: Session, payload: dict):
    obj = Project(**payload)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def update_project(db: Session, project_id: int, payload: dict):
    obj = get_project_by_id(db, project_id)
    if not obj:
        return None
    for key, value in payload.items():
        setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_project(db: Session, project_id: int):
    obj = get_project_by_id(db, project_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True
