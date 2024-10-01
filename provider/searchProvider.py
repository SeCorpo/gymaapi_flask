import logging
from typing import List, Optional

from sqlalchemy import or_, and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from model.Person import Person


def search_by_profile_url(db: Session, profile_url: str) -> Optional[List[Person]]:
    """ Return a list of all Persons that have the exact string in their profile_url. """
    try:
        # Use the LIKE operator to search for a substring match in profile_url
        persons = db.query(Person).filter(Person.profile_url.like(f"%{profile_url}%")).all()

        return persons if persons else None
    except SQLAlchemyError as e:
        logging.error(f"Error fetching persons by profile_url: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error finding Persons with query in their profile_url: {e}")
        return None


def search_by_first_and_last_name(db: Session, name: str) -> Optional[List[Person]]:
    """Return a list of all Persons that match the given first and last name in any order."""
    try:
        name_parts = name.split()

        if len(name_parts) != 2:
            return None

        first_name, last_name = name_parts

        prioritized_query = db.query(Person).filter(
            and_(Person.first_name.ilike(f"%{first_name}%"), Person.last_name.ilike(f"%{last_name}%"))
        ).all()

        non_prioritized_query = db.query(Person).filter(
            and_(Person.first_name.ilike(f"%{last_name}%"), Person.last_name.ilike(f"%{first_name}%"))
        ).all()

        persons = prioritized_query + [person for person in non_prioritized_query if person not in prioritized_query]

        return persons if persons else None

    except SQLAlchemyError as e:
        print(f"Error fetching persons by first and last name: {e}")
        return None
    except Exception as e:
        logging.error(f"Exception: Error finding Persons with query in their firstname and lastname: {e}")
        return None