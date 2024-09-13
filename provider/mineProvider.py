import logging
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, joinedload

from model.Gyma import Gyma
from model.GymaExercise import GymaExercise


def get_last_three_gyma_entry_of_user(db: Session, user_id: int, gyma_keys: str = None) -> List[Gyma]:
    """ Get last three gyma entries of a user by time_of_leaving, include associated exercises. """

    try:
        gyma_keys_to_exclude = gyma_keys.split(",") if gyma_keys else []

        query = (
            select(Gyma)
            .options(joinedload(Gyma.exercises).joinedload(GymaExercise.exercise))
            .order_by(desc(Gyma.time_of_leaving))
            .limit(3)
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
