import logging
from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import Session

from database import get_db
from dto.personDTO import PersonDTO, PersonSimpleDTO
from dto.profileDTO import ProfileDTO
from provider.authProvider import get_auth_key_or_none, get_auth_key
from service.friendshipService import get_friends_by_person_id, get_friendship, add_friendship, remove_friendship, \
    get_friendship_of_requester, update_friendship_status
from service.personService import get_person_by_profile_url, get_person_by_user_id
from session.sessionService import get_user_id_from_session_data

profile = Blueprint('profile', __name__, url_prefix='/api/v1/profile')


@profile.route("/<string:profile_url>", methods=["GET"])
def get_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key_or_none()

    logging.info("Get profile: %s", profile_url)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None or person_by_profile_url.gyma_share == "solo":
        abort(404, description="Profile does not exist")

    friendship_status = None
    user_id = None

    if auth_token is not None:
        user_id_from_session = get_user_id_from_session_data(auth_token)
        if user_id_from_session is not None:
            user_id = user_id_from_session

            friendship = get_friendship(db, user_id, person_by_profile_url.person_id)
            if friendship is not None:
                if friendship.status == "pending":
                    if friendship.friend_id == user_id:
                        friendship_status = "received"
                    else:
                        friendship_status = "pending"
                else:
                    friendship_status = friendship.status

    if person_by_profile_url.gyma_share == "gymbros" and (user_id is None or friendship_status != "accepted"):
        abort(403, description="Profile for friends only")

    friends = get_friends_by_person_id(db, person_by_profile_url.person_id)

    friend_list = [
        PersonSimpleDTO(
            profile_url=friend.profile_url,
            first_name=friend.first_name,
            last_name=friend.last_name,
            sex=friend.sex,
            pf_path_m=friend.pf_path_m
        ).model_dump()
        for friend in friends
    ]

    person_dto = PersonDTO(
        profile_url=person_by_profile_url.profile_url,
        first_name=person_by_profile_url.first_name,
        last_name=person_by_profile_url.last_name,
        date_of_birth=person_by_profile_url.date_of_birth,
        sex=person_by_profile_url.sex,
        city=person_by_profile_url.city,
        profile_text=person_by_profile_url.profile_text,
        pf_path_l=person_by_profile_url.pf_path_l,
        pf_path_m=person_by_profile_url.pf_path_m,
    ).model_dump()

    profile_dto = ProfileDTO(
        personDTO=person_dto,
        friend_list=friend_list,
        friendship_status=friendship_status
    ).model_dump()

    return jsonify(profile_dto), 200


@profile.route("/request/<string:profile_url>", methods=["GET"])
def add_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        abort(401, description="Session invalid")

    logging.info("Add friendship with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        abort(401, description="Create a profile first")

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        abort(404, description="Profile does not exist")
    if person_by_profile_url.gyma_share == "solo":
        abort(404, description="Profile not public")

    already_friend = get_friendship(db, user_id, person_by_profile_url.person_id)
    if already_friend:
        if already_friend.status == "accepted":
            abort(403, description="Friendship already accepted")
        elif already_friend.status == "pending":
            abort(403, description="Already requested")
        elif already_friend.status == "blocked":
            abort(403, description="Profile does not exist")

    friendship_ok = add_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_ok:
        return jsonify({"message": "Friendship request sent"}), 200
    else:
        abort(403, description="Unable to add friend")


@profile.route("/disconnect/<string:profile_url>", methods=["GET"])
def remove_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        abort(401, description="Session invalid")

    logging.info("Remove friendship with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        abort(401, description="Create a profile first")

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        abort(404, description="Profile does not exist")

    friendship_exists = get_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_exists is None:
        abort(403, description="Not a friend")
    if friendship_exists.status == "blocked":
        return jsonify({"message": "Already blocked"}), 200

    friendship_removed = remove_friendship(db, friendship_exists)
    if friendship_removed:
        return jsonify({"message": "Friend removed"}), 200
    else:
        abort(403, description="Unable to remove friend")


@profile.route("/accept/<string:profile_url>", methods=["GET"])
def accept_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        abort(401, description="Session invalid")

    logging.info("Accept friendship request with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        abort(401, description="Create a profile first")

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        abort(404, description="Profile does not exist")

    friendship_to_be_accepted = get_friendship_of_requester(db, person_by_profile_url.person_id, user_id)
    if friendship_to_be_accepted is None:
        abort(403, description="Friendship cannot be accepted")
    if friendship_to_be_accepted.status == "accepted":
        abort(403, description="Friendship already accepted")
    if friendship_to_be_accepted.status == "blocked":
        abort(403, description="Friendship cannot be accepted")

    friendship_accepted = update_friendship_status(db, friendship_to_be_accepted, "accepted")
    if friendship_accepted:
        return jsonify({"message": "Friendship accepted"}), 200
    else:
        abort(403, description="Unable to accept friend")


@profile.route("/block/<string:profile_url>", methods=["GET"])
def block_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        abort(401, description="Session invalid")

    logging.info("Block friendship request with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        abort(401, description="Create a profile first")

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        abort(404, description="Profile does not exist")

    friendship_to_be_blocked = get_friendship_of_requester(db, person_by_profile_url.person_id, user_id)
    if friendship_to_be_blocked is None:
        abort(403, description="Cannot block friendship before it starts")
    if friendship_to_be_blocked.status == "blocked":
        abort(403, description="Already blocked")

    friendship_blocked = update_friendship_status(db, friendship_to_be_blocked, "blocked")
    if friendship_blocked:
        return jsonify({"message": "Friendship blocked"}), 200
    else:
        abort(500, description="Unable to block person")
