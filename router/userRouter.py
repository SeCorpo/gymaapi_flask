import logging
from flask import Blueprint, request
from sqlalchemy.orm import Session

from database import get_db
from mail.emailService import send_verification_email
from service.userService import add_user, email_available
from dto.registerDTO import RegisterDTO
from service.userVerificationService import add_user_verification, generate_verification_code
from util.response import detail_response

user = Blueprint('user', __name__, url_prefix='/api/v1/user')


@user.route("", methods=["POST"])
def register():
    db: Session = next(get_db())
    register_dto = request.json

    logging.info(f"Trying to register user with email: {register_dto['email']}")

    if not email_available(db, register_dto['email']):
        return detail_response("Email is not available", 400)

    added_user = add_user(db, register_dto['email'], register_dto['password'])
    if added_user is None:
        return detail_response("Unable to create user", 400)

    verification_code = generate_verification_code(db)
    user_verification_added = add_user_verification(db, added_user.user_id, verification_code)
    if not user_verification_added:
        return detail_response("Unable to create user verification", 400)

    email_send = send_verification_email(verification_code, register_dto['email'])
    if email_send:
        return "true", 201
    else:
        return detail_response("Unable to send verification email", 400)
