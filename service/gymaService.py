import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy import select, desc
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from model.Gyma import Gyma
from model.GymaExercise import GymaExercise


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


def get_last_five_gyma_entry_of_user(db: Session, user_id: int, gyma_keys: str = None) -> List[Gyma]:
    """ Get last three gyma entries of a user by time_of_leaving, include associated exercises. """

    try:
        gyma_keys_to_exclude = gyma_keys.split(",") if gyma_keys else []

        query = (
            select(Gyma)
            .options(joinedload(Gyma.exercises).joinedload(GymaExercise.exercise))
            .order_by(desc(Gyma.time_of_leaving))
            .limit(5)
            .where(Gyma.user_id == user_id)
            .where(~Gyma.gyma_id.in_(gyma_keys_to_exclude))
            .where(Gyma.time_of_leaving.isnot(None))
        )

        result = db.execute(query)
        three_latest_gyma = result.scalars().unique().all()

        return list(three_latest_gyma)

    except Exception as e:
        logging.error(f"Error fetching gyma entries: {e}")
        return []
