from core.models import Users as ModelUser
from core.schema import User as SchemaUser
from db.database import SessionLocal
from fastapi import HTTPException, status
from psycopg2.errors import UniqueViolation

# error handling
from sqlalchemy.exc import IntegrityError

db = SessionLocal()


def add_user(user: SchemaUser):
    """Add a new user to the database
    :param user: User to add
    :return: newly added User"""
    try:
        user = ModelUser(uid=user.uid, username=user.username, email=user.email, role=user.role)
        db.add(user)
        db.commit()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e.orig).split("DETAIL:")[1])
        else:
            raise Exception(e)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return user


def get_user_token_info(uid: str):
    """Get user token info from the database
    :param uid: user id
    :return: tuple of user role and username"""
    try:
        result = db.query(ModelUser.role, ModelUser.username).filter(ModelUser.uid == uid).first()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve user")

    return result
