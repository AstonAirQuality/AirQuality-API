from core.models import Users as ModelUser
from core.schema import User as SchemaUser
from db.database import SessionLocal
from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

db = SessionLocal()


def add_user(user: SchemaUser):
    try:
        user = ModelUser(uid=user.uid, username=user.username, email=user.email, role=user.role)
        db.add(user)
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="SensorSummary already exists")
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return user


def get_user_role(uid: str):
    try:
        result = db.query(ModelUser.role).filter(ModelUser.uid == uid).first()
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could retrieve user")

    return result
