import logging
import string
import random
import redis
import pydantic
import os

from redis import RedisError
from dotenv import load_dotenv
from session.sessionDataObject import SessionDataObject

load_dotenv()

expire_time_default = int(os.getenv("SESSION_EXPIRE_TIME_SECONDS"))
expire_time_trust_device = int(os.getenv("SESSION_EXPIRE_TIME_SECONDS_TRUST_DEVICE"))
_redis_connection = None  # Cached Redis connection object


def create_redis_connection():
    """ Create and return a synchronous Redis connection object. """
    global _redis_connection
    if _redis_connection is None:
        redis_host = os.getenv("REDIS_HOST")
        redis_port = os.getenv("REDIS_PORT")
        redis_db = os.getenv("REDIS_DB", "0")
        redis_password = os.getenv("REDIS_PASSWORD")

        try:
            if redis_password:
                _redis_connection = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password,
                    decode_responses=True
                )
            else:
                _redis_connection = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
        except RedisError as e:
            logging.error(f"Error connecting to Redis: {e}")
            return None
        except Exception as e:
            logging.error(f"Other Exception while creating Redis connection: {e}")
            return None

    return _redis_connection


def get_session_data(key: str) -> SessionDataObject | None:
    """ Retrieve the session data as a SessionDataObject from Redis. """
    try:
        redis_connection = create_redis_connection()
        if not redis_connection:
            return None

        session_data = redis_connection.hgetall(key)
        if session_data:
            try:
                session_data['trustDevice'] = session_data.get('trustDevice') == '1'
                session_data_object = SessionDataObject(**session_data)
                expire_time = expire_time_trust_device if session_data_object.trustDevice else expire_time_default

                redis_connection.expire(key, expire_time)
                return session_data_object
            except pydantic.ValidationError as e:
                logging.error(f"Invalid session data format: {e}")
                return None
            except Exception as e:
                logging.error(f"Other Exception while getting session data: {e}")
                return None
        else:
            return None
    except RedisError as e:
        logging.error(f"RedisError while getting session data: {e}")
        return None
    except Exception as e:
        logging.error(f"Other Exception while getting session data: {e}")
        return None


def get_user_id_from_session_data(key: str) -> int | None:
    """ Get user ID from the session data stored in Redis. """
    try:
        session_data_object = get_session_data(key)
        if session_data_object:
            return session_data_object.user_id
        return None
    except pydantic.ValidationError as e:
        logging.error(f"Invalid session data format: {e}")
        return None
    except RedisError as e:
        logging.error(f"RedisError while getting user ID from session data: {e}")
        return None
    except Exception as e:
        logging.error(f"Other Exception while getting user ID from session data: {e}")
        return None


def get_gyma_id_from_session_data(key: str) -> int | None:
    """ Get gyma ID from the session data stored in Redis. """
    try:
        session_data_object = get_session_data(key)
        if session_data_object and session_data_object.gyma_id:
            return session_data_object.gyma_id
        return None
    except pydantic.ValidationError as e:
        logging.error(f"Invalid session data format: {e}")
        return None
    except Exception as e:
        logging.error(f"Other Exception while getting gyma ID from session data: {e}")
        return False


def set_session(session_data: SessionDataObject, key: str | None = None) -> str | None:
    """ Stores session data in Redis with a randomly generated key and expiration time. """
    try:
        redis_connection = create_redis_connection()
        if redis_connection is None:
            logging.error(f"Redis connection failed")
            return None

        if key is None:
            key = generate_random_key()

        data_dict = {k: (int(v) if isinstance(v, bool) else v) for k, v in session_data.dict().items() if v is not None}
        expire_time = expire_time_trust_device if session_data.trustDevice else expire_time_default

        redis_connection.hmset(key, data_dict)
        redis_connection.expire(key, expire_time)

        return key
    except RedisError as e:
        logging.error(f"Error setting session data in Redis: {e}")
        return None
    except Exception as e:
        logging.error(f"Other Exception while setting session data: {e}")
        return None


def set_gyma_id_in_session(key: str, gyma_id: int) -> bool:
    """ Adds gyma_id to the existing session data. """
    session_data = get_session_data(key)
    if session_data is None:
        return False

    session_data.gyma_id = gyma_id
    if set_session(session_data, key):
        return True

    logging.error("Unable to set gyma_id to session data")
    return False


def delete_gyma_id_from_session(key: str) -> bool:
    """ Deletes gyma_id from the existing session data. """
    session_data = get_session_data(key)
    if session_data is None or session_data.gyma_id is None:
        return False
    try:
        redis_connection = create_redis_connection()
        if redis_connection is None:
            logging.error("Redis connection failed")
            return False

        redis_connection.hdel(key, "gyma_id")
        expire_time = expire_time_trust_device if session_data.trustDevice else expire_time_default
        redis_connection.expire(key, expire_time)
        return True
    except RedisError as e:
        logging.error(f"Error deleting gyma_id from session data: {e}")
        return False
    except Exception as e:
        logging.error(f"Other Exception while deleting gyma_id from session: {e}")
        return False


def delete_session(key: str) -> bool:
    """ Deletes the session data from Redis. """
    try:
        redis_connection = create_redis_connection()
        if redis_connection is None:
            logging.error(f"Redis connection failed")
            return False

        if key and get_session_data(key):
            redis_connection.delete(key)
            logging.info(f"Deleted session data from Redis: {key}")
            return True

    except RedisError as e:
        logging.error(f"Error deleting session data in Redis (key: {key}): {e}")
        return False
    except Exception as e:
        logging.error(f"Other Exception while deleting session: {e}")
        return False


def generate_random_key(length: int = 16) -> str:
    """Generates a random alphanumeric string for use as a session key and ensures it is unique. """
    logging.info("Generating random key for session key")
    letters_and_digits = string.ascii_letters + string.digits
    key = ''.join(random.choice(letters_and_digits) for _ in range(length))

    if get_session_data(key) is None:
        return key
    else:
        return generate_random_key()
