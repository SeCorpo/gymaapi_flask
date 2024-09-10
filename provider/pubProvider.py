import logging
from typing import List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session, joinedload

from model.Gyma import Gyma
from model.GymaExercise import GymaExercise


def get_last_ten_gyma_entry(db: Session, gyma_keys: str = None) -> List[Gyma]:
    """ Get the last ten gyma entries by time_of_leaving, excluding those already fetched by the client. """

    try:
        gyma_keys_to_exclude = [key.strip() for key in (gyma_keys.split(",") if gyma_keys else [])]

        query = (
            select(Gyma)
            .options(joinedload(Gyma.exercises).joinedload(GymaExercise.exercise))
            .order_by(desc(Gyma.time_of_leaving))
            .limit(10)
            .where(Gyma.time_of_leaving.isnot(None))
        )

        if gyma_keys_to_exclude:
            query = query.where(~Gyma.gyma_id.in_(gyma_keys_to_exclude))

        result = db.execute(query)
        ten_latest_gyma = result.scalars().unique().all()

        return list(ten_latest_gyma)

    except Exception as e:
        logging.error(f"Error fetching gyma entries: {e}")
        return []
