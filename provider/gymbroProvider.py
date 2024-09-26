import logging
from typing import List
from sqlalchemy import select, desc, or_
from sqlalchemy.orm import Session, joinedload

from model.Friendship import Friendship
from model.Gyma import Gyma
from model.GymaExercise import GymaExercise


def get_last_ten_gyma_entries_of_user_and_friends(db: Session, user_id: int, gyma_keys: str = None) -> List[Gyma]:
    """ Get last ten gyma entries of user and user's friends by time_of_leaving,
    include associated exercises. """

    try:
        gyma_keys_to_exclude = gyma_keys.split(",") if gyma_keys else []

        # Fetch friend IDs of the user (ensure both person_id and friend_id are considered)
        friends_query = (
            select(Friendship.person_id, Friendship.friend_id)
            .where(
                or_(
                    Friendship.person_id == user_id,
                    Friendship.friend_id == user_id
                )
            )
            .where(Friendship.status == "accepted")
        )
        friends_result = db.execute(friends_query)

        # Collect friend IDs by checking which one is not the user_id
        friend_ids = set()  # use a set to avoid duplicates
        for row in friends_result.fetchall():
            if row[0] != user_id:
                friend_ids.add(row[0])  # person_id
            if row[1] != user_id:
                friend_ids.add(row[1])  # friend_id

        if not friend_ids:
            return []

        # Fetch the last 10 gyma entries, excluding those with keys in `gyma_keys_to_exclude`
        query = (
            select(Gyma)
            .options(joinedload(Gyma.exercises).joinedload(GymaExercise.exercise))
            .where(
                or_(
                    Gyma.user_id == user_id,
                    Gyma.user_id.in_(friend_ids)
                )
            )
            .where(~Gyma.gyma_id.in_(gyma_keys_to_exclude))
            .where(Gyma.time_of_leaving.isnot(None))
            .order_by(desc(Gyma.time_of_leaving))
            .limit(10)
        )

        result = db.execute(query)
        ten_latest_gyma = result.scalars().unique().all()

        return list(ten_latest_gyma)

    except Exception as e:
        logging.error(f"Error fetching gyma entries: {e}")
        return []
