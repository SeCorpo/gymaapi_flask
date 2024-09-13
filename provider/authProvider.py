import base64
import logging
from flask import request
from model.User import User
import bcrypt


def check_user_credentials(user: User, password: str) -> int | None:
    """Checking email and password credentials against database. Returns user ID or None."""
    if user is None or password is None:
        return None
    else:
        hashing_password = bcrypt.hashpw(password.encode('utf-8'), user.salt)
        if hashing_password == user.password_hash:
            return user.user_id
        else:
            return None


def get_auth_key() -> str | None:
    """Get decoded Authentication token from headers as a string."""
    authorization = request.headers.get('Authorization')

    if authorization:
        try:
            logging.info(f"Authorization header received: {authorization}")
            decoded_key = decode_str(authorization)
            logging.info(f"Decoded key: {decoded_key}")
            return decoded_key
        except Exception as e:
            logging.error(f"Error decoding authentication key: {e}")
            return None
    logging.error("Authentication credentials were not provided.")
    return None


def encode_str(text: str) -> str:
    """Encode a string using base64. Used for sending encoded session_token to client."""
    encoded_bytes = base64.b64encode(text.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    return encoded_str


def decode_str(encoded_str: str) -> str:
    """Decode a base64 encoded string."""
    decoded_bytes = base64.b64decode(encoded_str.encode('utf-8'))
    decoded_str = decoded_bytes.decode('utf-8')
    return decoded_str
