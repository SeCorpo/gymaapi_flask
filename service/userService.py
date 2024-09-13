import logging
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
import bcrypt
from model.User import User


def add_user(db: Session, email: str, password: str) -> User | None:
    """ Registers a new user to database. """
    try:
        salt, hashed_password = password_hasher(password)

        new_user = User(
            email=email,
            salt=salt,
            password_hash=hashed_password,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except SQLAlchemyError as e:
        logging.error(f"Error adding user: {e}")
        db.rollback()
        return None
    except Exception as e:
        logging.error(f"Exception: Error adding user: {e}")
        db.rollback()
        return None


def get_user_by_user_id(db: Session, user_id: int) -> User | None:
    """ Get User object by user id from database. """
    try:
        result = db.execute(select(User).filter_by(user_id=user_id))
        user = result.scalar_one_or_none()
        return user
    except NoResultFound:
        logging.error(f"No user found with user_id: {user_id}")
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching user by ID: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error fetching user by ID: {e}")
        return None


def get_user_by_email(db: Session, email: str) -> User | None:
    """ Get User object by email from database. """
    try:
        result = db.execute(select(User).filter_by(email=email))
        user = result.scalar_one_or_none()
        return user
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching user by email: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error fetching user by email: {e}")
        return None


def email_available(db: Session, email: str) -> bool:
    """ Check if email is already registered. """
    try:
        result = db.execute(select(User).filter_by(email=email))
        user_exists = result.scalar_one_or_none()
        return user_exists is None
    except SQLAlchemyError as e:
        logging.error(f"Error checking email availability: {e}")
        return False
    except Exception as e:
        logging.error(f"Exception: Error checking email availability: {e}")
        return False


def password_hasher(password_plain: str) -> (bytes, bytes):
    """ Hashes a password using bcrypt and generates a random salt. """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_plain.encode('utf-8'), salt)
    return salt, hashed_password


def set_email_verification(db: Session, user: User, verified: bool = True) -> bool:
    """ Change the value of email_verification, a user needs to be email verified to be able to log in. """
    try:
        user.email_verified = verified
        db.commit()
        return True
    except SQLAlchemyError as e:
        logging.error(f"Error setting email verification: {e}")
        db.rollback()
        return False
    except Exception as e:
        logging.error(f"Exception: Error setting email verification: {e}")
        db.rollback()
        return False
