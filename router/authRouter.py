import os
from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import Session
import logging

from database import get_db
from dto.personDTO import PersonDTO, PersonSimpleDTO
from dto.profileDTO import MyProfileDTO
from mail.emailService import send_verification_email
from provider.authProvider import check_user_credentials, encode_str, get_auth_key
from dto.loginDTO import LoginDTO, LoginResponseDTO
from service.friendshipService import get_friends_by_person_id, get_pending_friendships_to_be_accepted
from service.personService import get_person_by_user_id
from service.userService import get_user_by_email, get_user_by_user_id, set_email_verification
from service.userVerificationService import get_user_id_by_verification_code, remove_user_verification, get_verification_code_by_user_id
from session.sessionService import set_session, delete_session
from session.sessionDataObject import SessionDataObject
from util.response import detail_response

API_URL = os.getenv("API_BASE_URL")
auth = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

@auth.route("/login", methods=['POST'])
def login():
    db: Session = next(get_db())
    login_dto = request.json

    logging.info(f"Attempting login for user with email: {login_dto['email']}")

    user = get_user_by_email(db, login_dto['email'])
    if user is None:
        return detail_response("User not found", 400)

    user_id_of_ok_credentials = check_user_credentials(user, login_dto['password'])
    if user_id_of_ok_credentials is None:
        return detail_response("Incorrect email or password", 401)

    if not user.email_verified:
        return detail_response("Email not verified. Please check your email to verify your account.", 403)

    session_object_only_user_id = SessionDataObject(user_id=user_id_of_ok_credentials, trustDevice=login_dto.get('trustDevice', False))
    raw_session_key = set_session(session_object_only_user_id)
    if raw_session_key is None:
        return detail_response("Unable to login, please try later", 500)

    person = get_person_by_user_id(db, user_id_of_ok_credentials)
    encoded_session_key = encode_str(raw_session_key)

    if person is not None:
        friends = get_friends_by_person_id(db, person.person_id)
        friend_list = [
            PersonSimpleDTO(
                profile_url=friend.profile_url,
                first_name=friend.first_name,
                last_name=friend.last_name,
                sex=friend.sex,
                pf_path_m=f"{API_URL}/images/medium/{friend.pf_path_m}" if friend.pf_path_m else None,
            ).model_dump(mode='json')
            for friend in friends
        ]

        pf_path_l = f"{API_URL}/images/large/{person.pf_path_l}" if person.pf_path_l else None
        pf_path_m = f"{API_URL}/images/medium/{person.pf_path_m}" if person.pf_path_m else None

        person_dto = PersonDTO(
            profile_url=person.profile_url,
            first_name=person.first_name,
            last_name=person.last_name,
            date_of_birth=person.date_of_birth,
            sex=person.sex,
            city=person.city,
            profile_text=person.profile_text,
            pf_path_l=pf_path_l,
            pf_path_m=pf_path_m,
        ).model_dump(mode='json')

        pending_friends = get_pending_friendships_to_be_accepted(db, user_id_of_ok_credentials)
        pending_friend_list = [
            PersonSimpleDTO(
                profile_url=friend.profile_url,
                first_name=friend.first_name,
                last_name=friend.last_name,
                sex=friend.sex,
                pf_path_m=f"{API_URL}/images/medium/{friend.pf_path_m}" if friend.pf_path_m else None,
            ).model_dump(mode='json')
            for friend in pending_friends
        ]

        my_profile_dto = MyProfileDTO(
            personDTO=person_dto,
            friend_list=friend_list,
            pending_friend_list=pending_friend_list
        ).model_dump(mode='json')
    else:
        my_profile_dto = None

    return jsonify({
        "session_token": encoded_session_key,
        "myProfileDTO": my_profile_dto,
        "device_trusted": login_dto.get('trustDevice', False),
    }), 200


@auth.route("/logout", methods=['POST'])
def logout():
    auth_token = get_auth_key()
    logging.info("Attempting logout and session deletion")
    if auth_token is None:
        return detail_response("Session does not exist", 404)
    else:
        result = delete_session(auth_token)
        return jsonify(result), 200


@auth.route("/verify/<verification_code>", methods=['GET'])
def verify(verification_code: str):
    db: Session = next(get_db())
    logging.info("Attempting email verification with verification code")
    user_id = get_user_id_by_verification_code(db, verification_code)
    logging.info(f"Verification code: {verification_code}")
    if user_id is None:
        return detail_response("Verification code does not exist", 404)

    else:
        logging.info(f"Verifying user {user_id}")
        user = get_user_by_user_id(db, user_id)
        if user is None:
            return detail_response("User not found", 404)

        else:
            verification_code_removed = remove_user_verification(db, user_id)
            email_verified = set_email_verification(db, user)
            if email_verified is True and verification_code_removed is True:
                return "true", 200
            else:
                return detail_response("Unable to verify email, please contact support", 403)


@auth.route("/resend_verification_mail", methods=['POST'])
def resend_verification():
    db: Session = next(get_db())
    login_dto = request.json

    logging.info(f"Attempting email resend: {login_dto['email']}")
    if login_dto['email'] is None:
        return detail_response("Please provide email", 404)

    else:
        user_of_email = get_user_by_email(db, login_dto['email'])
        if user_of_email is None:
            return detail_response("User not found", 400)

        elif user_of_email.email_verified:
            return detail_response("User already verified", 403)

        else:
            verification_code_from_user_id = get_verification_code_by_user_id(db, user_of_email.user_id)
            if verification_code_from_user_id is None:
                return detail_response("Verification code does not exist, please contact support", 404)

            else:
                email_send = send_verification_email(verification_code_from_user_id, login_dto['email'])
                if email_send:
                    return "true", 200
                else:
                    return detail_response("Unable to send verification email", 400)
