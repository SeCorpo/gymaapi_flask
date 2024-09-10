import logging
from datetime import datetime
from typing import Optional

from flask import abort
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


def add_gyma(db: Session, user_id: Optional[int]) -> Optional[Gyma]:
    """ Add new Gyma to database. """
    if user_id is None:
        raise Exception("Gyma requires a person_id")

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
            abort(404, description="Gyma cannot be found")

        if gyma.user_id != user_id:
            abort(403, description="Gyma can only be altered by its owner")

        if gyma.time_of_leaving is not None:
            abort(400, description="Gyma time_of_leaving has already been set")

        gyma.time_of_leaving = datetime.now()
        db.commit()
        db.refresh(gyma)
        return gyma.time_of_leaving

    except SQLAlchemyError as e:
        logging.error(f"Error setting time of leaving: {e}")
        db.rollback()
        return None
