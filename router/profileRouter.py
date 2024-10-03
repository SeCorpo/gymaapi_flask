import logging
import os
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session

from database import get_db
from dto.exerciseDTO import ExerciseDTO
from dto.gymaDTO import GymaDTO
from dto.personDTO import PersonDTO, PersonSimpleDTO
from dto.profileDTO import ProfileDTO, MyProfileUpdateListsDTO
from provider.authProvider import get_auth_key
from service.friendshipService import get_friends_by_person_id, get_friendship, add_friendship, remove_friendship, \
    get_friendship_of_requester, update_friendship_status, block_friendship, get_pending_friendships_to_be_accepted, \
    get_blocked_friendships
from service.gymaService import get_last_five_gyma_entry_of_user
from service.personService import get_person_by_profile_url, get_person_by_user_id
from session.sessionService import get_user_id_from_session_data
from util.response import detail_response

API_URL = os.getenv("API_BASE_URL")
profile = Blueprint('profile', __name__, url_prefix='/api/v1/profile')

@profile.route("/<string:profile_url>", methods=["GET"])
def get_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    logging.info("Get profile: %s", profile_url)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None or person_by_profile_url.gyma_share == "solo":
        return detail_response("Profile does not exist", 404)

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
                elif friendship.status == "blocked":
                    return detail_response("Profile does not exist", 404)
                else:
                    friendship_status = friendship.status

    if person_by_profile_url.gyma_share == "gymbros" and (user_id is None or friendship_status != "accepted"):
        return detail_response("Profile for friends only", 403)

    friends = get_friends_by_person_id(db, person_by_profile_url.person_id)

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

    pf_path_l = f"{API_URL}/images/large/{person_by_profile_url.pf_path_l}" if person_by_profile_url.pf_path_l else None
    pf_path_m = f"{API_URL}/images/medium/{person_by_profile_url.pf_path_m}" if person_by_profile_url.pf_path_m else None

    person_dto = PersonDTO(
        profile_url=person_by_profile_url.profile_url,
        first_name=person_by_profile_url.first_name,
        last_name=person_by_profile_url.last_name,
        date_of_birth=person_by_profile_url.date_of_birth,
        sex=person_by_profile_url.sex,
        city=person_by_profile_url.city,
        profile_text=person_by_profile_url.profile_text,
        pf_path_l=pf_path_l,
        pf_path_m=pf_path_m,
    ).model_dump(mode='json')

    five_latest_gyma = get_last_five_gyma_entry_of_user(db, person_by_profile_url.person_id)

    person_simple_dto = PersonSimpleDTO(
        profile_url=person_by_profile_url.profile_url,
        first_name=person_by_profile_url.first_name,
        last_name=person_by_profile_url.last_name,
        sex=person_by_profile_url.sex,
        pf_path_m=f"{API_URL}/images/medium/{person_by_profile_url.pf_path_m}" if person_by_profile_url.pf_path_m else None,
    ).model_dump(mode='json')

    gyma_with_exercises = []
    for gyma in five_latest_gyma:
        exercise_dtos = [
            ExerciseDTO(
                exercise_id=exercise.exercise_id,
                exercise_name=exercise.exercise.exercise_name,
                exercise_type=exercise.exercise.exercise_type,
                count=exercise.exercise.count,
                sets=exercise.exercise.sets,
                weight=exercise.exercise.weight,
                minutes=exercise.exercise.minutes,
                km=exercise.exercise.km,
                level=exercise.exercise.level,
                description=exercise.exercise.description,
            ).model_dump(mode='json')
            for exercise in gyma.exercises
        ]

        gyma_dto = GymaDTO(
            gyma_id=gyma.gyma_id,
            person=person_simple_dto,
            time_of_arrival=gyma.time_of_arrival,
            time_of_leaving=gyma.time_of_leaving,
            exercises=exercise_dtos
        ).model_dump(mode='json')

        gyma_with_exercises.append(gyma_dto)

    profile_dto = ProfileDTO(
        personDTO=person_dto,
        gyma_list=gyma_with_exercises,
        friend_list=friend_list,
        friendship_status=friendship_status
    ).model_dump(mode='json')

    return jsonify(profile_dto), 200


@profile.route("/update_lists", methods=["GET"])
def update_my_profile_lists():
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    friends = get_friends_by_person_id(db, user_id)
    friend_list = [
        PersonSimpleDTO(
            profile_url=friend.profile_url,
            first_name=friend.first_name,
            last_name=friend.last_name,
            sex=friend.sex,
            pf_path_m=f"{API_URL}/images/medium/{friend.pf_path_m}" if friend.pf_path_m else None,
        )
        for friend in friends
    ]

    pending_friends = get_pending_friendships_to_be_accepted(db, user_id)
    pending_friend_list = [
        PersonSimpleDTO(
            profile_url=friend.profile_url,
            first_name=friend.first_name,
            last_name=friend.last_name,
            sex=friend.sex,
            pf_path_m=f"{API_URL}/images/medium/{friend.pf_path_m}" if friend.pf_path_m else None,
        )
        for friend in pending_friends
    ]

    blocked_friends = get_blocked_friendships(db, user_id)
    blocked_friend_list = [
        PersonSimpleDTO(
            profile_url=friend.profile_url,
            first_name=friend.first_name,
            last_name=friend.last_name,
            sex=friend.sex,
            pf_path_m=f"{API_URL}/images/medium/{friend.pf_path_m}" if friend.pf_path_m else None,
        )
        for friend in blocked_friends
    ]

    profile_update_dto = MyProfileUpdateListsDTO(
        friend_list=friend_list,
        pending_friend_list=pending_friend_list,
        blocked_friend_list=blocked_friend_list,
    )

    return jsonify(profile_update_dto.model_dump()), 200


@profile.route("/<string:profile_url>/moregyma", methods=["POST"])
def get_five_more_gyma_of_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()
    gyma_keys = request.get_json()

    logging.info("Get profile: %s", profile_url)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None or person_by_profile_url.gyma_share == "solo":
        return detail_response("Profile does not exist", 404)

    user_id = None
    friendship_status = None

    if auth_token is not None:
        user_id_from_session = get_user_id_from_session_data(auth_token)
        if user_id_from_session is not None:
            user_id = user_id_from_session

            if user_id == person_by_profile_url.person_id:

                person_simple_dto = PersonSimpleDTO(
                    profile_url=person_by_profile_url.profile_url,
                    first_name=person_by_profile_url.first_name,
                    last_name=person_by_profile_url.last_name,
                    sex=person_by_profile_url.sex,
                    pf_path_m=f"{API_URL}/images/medium/{person_by_profile_url.pf_path_m}" if person_by_profile_url.pf_path_m else None,
                ).model_dump(mode='json')

                five_more_my_gyma = get_last_five_gyma_entry_of_user(db, user_id, gyma_keys)

                gyma_with_exercises = []
                for gyma in five_more_my_gyma:
                    exercise_dtos = [
                        ExerciseDTO(
                            exercise_id=exercise.exercise.exercise_id,
                            exercise_name=exercise.exercise.exercise_name,
                            exercise_type=exercise.exercise.exercise_type,
                            count=exercise.exercise.count,
                            sets=exercise.exercise.sets,
                            weight=exercise.exercise.weight,
                            minutes=exercise.exercise.minutes,
                            km=exercise.exercise.km,
                            level=exercise.exercise.level,
                            description=exercise.exercise.description,
                        ).model_dump(mode='json')
                        for exercise in gyma.exercises
                    ]

                    gyma_dto = GymaDTO(
                        gyma_id=gyma.gyma_id,
                        person=person_simple_dto,
                        time_of_arrival=gyma.time_of_arrival,
                        time_of_leaving=gyma.time_of_leaving,
                        exercises=exercise_dtos
                    ).model_dump(mode='json')

                    gyma_with_exercises.append(gyma_dto)
                return gyma_with_exercises, 200


            friendship = get_friendship(db, user_id, person_by_profile_url.person_id)
            if friendship is not None:
                if friendship.status == "pending":
                    friendship_status = "received" if friendship.friend_id == user_id else "pending"
                elif friendship.status == "blocked":
                    return detail_response("Profile does not exist", 404)
                else:
                    friendship_status = friendship.status


    if person_by_profile_url.gyma_share == "gymbros" and (user_id is None or friendship_status != "accepted"):
        return detail_response("Profile for friends only", 403)

    person_simple_dto = PersonSimpleDTO(
        profile_url=person_by_profile_url.profile_url,
        first_name=person_by_profile_url.first_name,
        last_name=person_by_profile_url.last_name,
        sex=person_by_profile_url.sex,
        pf_path_m=f"{API_URL}/images/medium/{person_by_profile_url.pf_path_m}" if person_by_profile_url.pf_path_m else None,
    ).model_dump(mode='json')

    five_more_gyma = get_last_five_gyma_entry_of_user(db, person_by_profile_url.person_id, gyma_keys)

    gyma_with_exercises = []
    for gyma in five_more_gyma:
        exercise_dtos = [
            ExerciseDTO(
                exercise_id=exercise.exercise.exercise_id,
                exercise_name=exercise.exercise.exercise_name,
                exercise_type=exercise.exercise.exercise_type,
                count=exercise.exercise.count,
                sets=exercise.exercise.sets,
                weight=exercise.exercise.weight,
                minutes=exercise.exercise.minutes,
                km=exercise.exercise.km,
                level=exercise.exercise.level,
                description=exercise.exercise.description,
            ).model_dump(mode='json')
            for exercise in gyma.exercises
        ]

        gyma_dto = GymaDTO(
            gyma_id=gyma.gyma_id,
            person=person_simple_dto,
            time_of_arrival=gyma.time_of_arrival,
            time_of_leaving=gyma.time_of_leaving,
            exercises=exercise_dtos
        ).model_dump(mode='json')

        gyma_with_exercises.append(gyma_dto)
    return gyma_with_exercises, 200


@profile.route("/request/<string:profile_url>", methods=["GET"])
def add_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    logging.info("Add friendship with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        return detail_response("Profile does not exist", 404)
    if person_by_profile_url.gyma_share == "solo":
        return detail_response("Profile not public", 404)

    already_friend = get_friendship(db, user_id, person_by_profile_url.person_id)
    if already_friend:
        if already_friend.status == "accepted":
            return detail_response("Friendship already accepted", 403)
        elif already_friend.status == "pending":
            return detail_response("Already requested", 403)
        elif already_friend.status == "blocked":
            return detail_response("Profile does not exist", 403)

    friendship_ok = add_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_ok:
        return "true", 200
    else:
        return detail_response("Unable to add friend", 403)


@profile.route("/disconnect/<string:profile_url>", methods=["GET"])
def remove_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    logging.info("Remove friendship with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        return detail_response("Profile does not exist", 404)

    friendship_exists = get_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_exists is None:
        return detail_response("Not a friend", 403)
    if friendship_exists.status == "blocked":
        return "true", 200

    friendship_removed = remove_friendship(db, friendship_exists)
    if friendship_removed:
        return "true", 200
    else:
        return detail_response("Unable to remove friend", 403)


@profile.route("/accept/<string:profile_url>", methods=["GET"])
def accept_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    logging.info("Accept friendship request with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        return detail_response("Profile does not exist", 404)

    friendship_to_be_accepted = get_friendship_of_requester(db, person_by_profile_url.person_id, user_id)
    if friendship_to_be_accepted is None:
        return detail_response("Friendship cannot be accepted", 403)
    if friendship_to_be_accepted.status == "accepted":
        return detail_response("Friendship already accepted", 403)
    if friendship_to_be_accepted.status == "blocked":
        return detail_response("Friendship cannot be accepted", 403)

    friendship_accepted = update_friendship_status(db, friendship_to_be_accepted, "accepted")
    if friendship_accepted:
        return "true", 200
    else:
        return detail_response("Unable to accept friend", 403)


@profile.route("/block/<string:profile_url>", methods=["GET"])
def block_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    logging.info("Block friendship request with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        return detail_response("Profile does not exist", 404)

    friendship_to_be_blocked = get_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_to_be_blocked is None:
        return detail_response("Cannot block friendship before it starts", 403)
    if friendship_to_be_blocked.status == "blocked":
        return detail_response("Already blocked", 403)

    friendship_blocked = block_friendship(db, friendship_to_be_blocked, user_id)
    if friendship_blocked:
        return "true", 200
    else:
        return detail_response("Unable to block person", 500)


@profile.route("/unblock/<string:profile_url>", methods=["GET"])
def unblock_friend_by_profile(profile_url):
    db: Session = next(get_db())
    auth_token = get_auth_key()

    if auth_token is None:
        return detail_response("Session invalid", 401)

    logging.info("Unblock friendship request with profile url: %s", profile_url)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    requester_has_profile = get_person_by_user_id(db, user_id)
    if requester_has_profile is None:
        return detail_response("Create a profile first", 401)

    person_by_profile_url = get_person_by_profile_url(db, profile_url)
    if person_by_profile_url is None:
        return detail_response("Profile does not exist", 404)

    friendship_to_be_unblocked = get_friendship(db, user_id, person_by_profile_url.person_id)
    if friendship_to_be_unblocked is None:
        return detail_response("No friendship to unblock", 403)
    if friendship_to_be_unblocked.status != "blocked":
        return detail_response("This person is not blocked", 403)

    removed_friendship = remove_friendship(db, friendship_to_be_unblocked)
    if removed_friendship:
        return "true", 200
    else:
        return detail_response("Unable to unblock friendship", 400)
