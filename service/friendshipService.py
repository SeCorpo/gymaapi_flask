import logging
from datetime import date

from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload, Session

from model.Friendship import Friendship
from model.Person import Person


def get_friends_by_person_id(db: Session, person_id: int) -> list[Person]:
    """ Get all accepted friends for a given person by their person_id. """
    result = db.execute(
        select(Person).join(Person.friends).where(
            and_(
                or_(
                    and_(Friendship.person_id == person_id, Friendship.status == "accepted"),
                    and_(Friendship.friend_id == person_id, Friendship.status == "accepted")
                ),
                Person.person_id != person_id
            )
        ).options(joinedload(Person.friends)).distinct()
    )
    return list(result.scalars().unique().all())


def get_friendship(db: Session, person_id: int, friend_id: int) -> Friendship | None:
    """ Get friendship connection. """
    try:
        if person_id == friend_id:
            logging.error("Cannot have friendship connection with oneself")
            return None

        logging.info(f"Getting friendship for {person_id} and {friend_id}")
        result = db.execute(
            select(Friendship).where(
                or_(
                    and_(Friendship.person_id == person_id, Friendship.friend_id == friend_id),
                    and_(Friendship.person_id == friend_id, Friendship.friend_id == person_id)
                )
            )
        )
        friendship = result.scalar_one_or_none()
        return friendship
    except Exception as e:
        logging.error(f"Failed to get friendship: {e}")
        return None


def get_friendship_of_requester(db: Session, person_id: int, friend_id: int) -> Friendship | None:
    """ Get friendship object; person_id is the requesting party, friend_id is the receiving party. """
    try:
        result = db.execute(
            select(Friendship).where(
                and_(Friendship.person_id == person_id, Friendship.friend_id == friend_id)
            )
        )
        friendship = result.scalar_one_or_none()
        return friendship
    except Exception as e:
        logging.error(f"Failed to get friendship of requester: {e}")
        return None


def add_friendship(db: Session, person_id: int, friend_id: int) -> bool:
    """ Add a new friendship. """
    try:
        new_friendship = Friendship(
            person_id=person_id,
            friend_id=friend_id,
            status='pending',
            since=date.today()
        )
        db.add(new_friendship)
        db.commit()
        db.refresh(new_friendship)
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to add friendship: {e}")
        return False


def update_friendship_status(db: Session, friendship: Friendship, status: str) -> bool:
    """ Update the status of a friendship. """
    try:
        friendship.status = status
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to update friendship status: {e}")
        return False

def block_friendship(db: Session, friendship: Friendship, person_id: int) -> bool:
    """ This function makes sure to make the blocking person the primary (initiating) party of the friendship. """
    try:
        if friendship.person_id != person_id:
            friendship.person_id, friendship.friend_id = friendship.friend_id, friendship.person_id

        friendship.status = "blocked"
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Error blocking friendship: {e}")
        return False


def remove_friendship(db: Session, friendship: Friendship) -> bool:
    """ Remove a friendship. """
    try:
        db.delete(friendship)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to remove friendship: {e}")
        return False


def get_pending_friendships_to_be_accepted(db: Session, person_id: int) -> list[Person]:
    """ Get all persons who have sent pending friendship requests to the given person. """
    result = db.execute(
        select(Person).join(Friendship, Friendship.person_id == Person.person_id).where(
            and_(
                Friendship.friend_id == person_id,
                Friendship.status == 'pending'
            )
        ).options(joinedload(Person.friends)).distinct()
    )
    return list(result.scalars().unique().all())


def get_blocked_friendships(db: Session, person_id: int) -> list[Person]:
    """ Get all persons blocked by person_id. """
    result = db.execute(
        select(Person).join(Person.friends).where(
            and_(
                Friendship.person_id == person_id,
                Friendship.status == 'blocked',
                Person.person_id != person_id
            ),
        ).options(joinedload(Person.friends)).distinct()
    )
    return list(result.scalars().unique().all())
