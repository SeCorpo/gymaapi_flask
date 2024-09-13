import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from model.Gyma import Gyma


def get_gyma_by_gyma_id(db: Session, gyma_id: int) -> Optional[Gyma]:
    """ Get Gyma object by gyma id from database. """
    try:
        result = db.execute(select(Gyma).filter_by(gyma_id=gyma_id))
        gyma = result.scalar_one_or_none()
        return gyma
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching gyma by ID: {e}")
        return None


def add_gyma(db: Session, user_id: int) -> Optional[Gyma]:
    """ Add new Gyma to database. """
    try:
        new_gyma = Gyma(
            user_id=user_id,
            time_of_arrival=datetime.now()
        )
        db.add(new_gyma)
        db.commit()
        db.refresh(new_gyma)
        return new_gyma
    except SQLAlchemyError as e:
        logging.error(f"Error adding gyma: {e}")
        db.rollback()
        return None


def set_time_of_leaving(db: Session, user_id: int, gyma: Gyma) -> Optional[datetime]:
    """ Time of leaving the gyma. """
    try:
        if gyma is None:
            logging.error("Gyma cannot be found")
            return None

        if gyma.user_id != user_id:
            logging.error("Gyma can only be altered by its owner")
            return None

        if gyma.time_of_leaving is not None:
            logging.error("Gyma time_of_leaving has already been set")
            return None

        gyma.time_of_leaving = datetime.now()
        db.commit()
        db.refresh(gyma)
        return gyma.time_of_leaving

    except SQLAlchemyError as e:
        logging.error(f"Error setting time of leaving: {e}")
        db.rollback()
        return None
