import logging
import random
import string

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from model.UserVerification import UserVerification


def get_user_id_by_verification_code(db: Session, verification_code: str) -> int | None:
    """ Get user id from verification code. """
    try:
        result = db.execute(select(UserVerification).filter_by(verification_code=verification_code))
        user_verification = result.scalar_one_or_none()
        if user_verification:
            return user_verification.user_id
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching user by verification code: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error fetching user by verification code: {e}")
        return None


def get_verification_code_by_user_id(db: Session, user_id: int) -> str | None:
    """ Get verification code from user id. """
    try:
        result = db.execute(select(UserVerification).filter_by(user_id=user_id))
        user_verification = result.scalar_one_or_none()
        if user_verification:
            return user_verification.verification_code
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching verification code by user ID: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error fetching verification code by user ID: {e}")
        return None


def add_user_verification(db: Session, user_id: int, verification_code: str) -> bool:
    """ Add user_verification to database. Which is made after registering a user to verify its email address. """
    try:
        user_verification = UserVerification(user_id=user_id, verification_code=verification_code)
        db.add(user_verification)
        db.commit()
        return True
    except SQLAlchemyError as e:
        logging.error(f"Error adding user verification: {e}")
        db.rollback()
        return False
    except Exception as e:
        logging.error(f"Exception: Error adding user verification: {e}")
        db.rollback()
        return False


def remove_user_verification(db: Session, user_id: int) -> bool:
    """ Remove user_verification from database. """
    try:
        result = db.execute(select(UserVerification).filter_by(user_id=user_id))
        user_verification = result.scalar_one_or_none()

        if user_verification:
            db.delete(user_verification)
            db.commit()
            return True
        else:
            logging.error(f"No user verification found for user_id: {user_id}")
            return False
    except SQLAlchemyError as e:
        logging.error(f"Error removing user verification: {e}")
        db.rollback()
        return False
    except Exception as e:
        logging.error(f"Exception: Error removing user verification: {e}")
        db.rollback()
        return False


def generate_verification_code(db: Session) -> str:
    """ Generates a random alphanumeric string for use as a verification_code and makes sure it's not already used.  """
    letters_and_digits = string.ascii_letters + string.digits
    verification_code = ''.join(random.choice(letters_and_digits) for _ in range(64))

    if get_user_id_by_verification_code(db, verification_code) is None:
        return verification_code
    else:
        return generate_verification_code(db)
