import logging
import os
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from dto.imageDTO import ImageDTO
from dto.personDTO import PersonDTO, EnterPersonDTO, PersonSimpleDTO
from dto.profileDTO import MyProfileDTO
from provider.authProvider import get_auth_key
from provider.imageProvider import process_image, move_images_to_archive
from provider.searchProvider import search_by_profile_url, search_by_first_and_last_name
from service.personService import add_person, get_person_by_user_id, edit_person, set_pf_paths
from session.sessionService import get_user_id_from_session_data
from util.response import detail_response

person = Blueprint('person', __name__, url_prefix='/api/v1/person')
API_URL = os.getenv("API_BASE_URL")


@person.route("", methods=["POST"])
def add_or_edit_person():
    db: Session = next(get_db())
    auth_token = get_auth_key()

    try:
        enter_person_dto = EnterPersonDTO(**request.json)
    except ValidationError as e:
        logging.error(f"Validation Error: {e}")
        return detail_response("Invalid data format", 400)

    logging.info("Creating or editing person object for user")

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    person_obj = get_person_by_user_id(db, user_id)
    if person_obj is None:
        logging.info("Creating person object for user")
        new_person = add_person(db, user_id, enter_person_dto)
        if new_person is None:
            return detail_response("Person cannot be created", 400)

        else:
            person_dto = PersonDTO(
                profile_url=new_person.profile_url,
                first_name=new_person.first_name,
                last_name=new_person.last_name,
                date_of_birth=new_person.date_of_birth,
                sex=new_person.sex,
                city=new_person.city,
                profile_text=new_person.profile_text,
                pf_path_l=new_person.pf_path_l, # will be None
                pf_path_m=new_person.pf_path_m, # will be None
            ).model_dump(mode='json')
            my_profile_dto = MyProfileDTO(
                personDTO=person_dto,
                friend_list=[],
                pending_friend_list=[]
            ).model_dump(mode='json')
            return jsonify(my_profile_dto), 200
    else:
        logging.info("Updating person object for user")
        edited_person = edit_person(db, user_id, person_obj, enter_person_dto)
        if edited_person is None:
            return detail_response("Person cannot be updated", 400)

        else:
            person_dto = PersonDTO(
                profile_url=edited_person.profile_url,
                first_name=edited_person.first_name,
                last_name=edited_person.last_name,
                date_of_birth=edited_person.date_of_birth,
                sex=edited_person.sex,
                city=edited_person.city,
                profile_text=edited_person.profile_text,
                pf_path_l=f"{API_URL}/images/large/{edited_person.pf_path_l}" if edited_person.pf_path_l else None,
                pf_path_m=f"{API_URL}/images/medium/{edited_person.pf_path_m}" if edited_person.pf_path_m else None,
            ).model_dump(mode='json')
            my_profile_dto = MyProfileDTO(
                personDTO=person_dto,
                friend_list=[],
                pending_friend_list=[]
            ).model_dump(mode='json')
            logging.info(my_profile_dto)
            return jsonify(my_profile_dto), 200


@person.route("/picture", methods=["POST"])
def upload_picture():
    db: Session = next(get_db())
    auth_token = get_auth_key()
    file = request.files.get('file')

    if not file:
        return detail_response("No file provided", 403)

    logging.info("Processing picture for user")

    try:
        image_dto = ImageDTO(file=file)
        image_dto.validate_file(file)
    except ValueError as e:
        return detail_response("Invalid data format", 400)

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    person_obj = get_person_by_user_id(db, user_id)
    if person_obj is None:
        return detail_response("Picture cannot be added if there is no person", 404)

    if person_obj.pf_path_l and person_obj.pf_path_m is not None:
        logging.info("Archiving previous picture of user")
        move_ok = move_images_to_archive(person_obj.pf_path_l, person_obj.pf_path_m)
        if not move_ok:
            return detail_response("Picture cannot be moved to archive", 500)

    picture_names = process_image(image_dto)
    if picture_names is None:
        return detail_response("Picture cannot be processed, please try a different picture", 400)

    person_with_pf_paths = set_pf_paths(db, person_obj, picture_names["pf_path_l"], picture_names["pf_path_m"])
    if not person_with_pf_paths:
        return detail_response("New pictures cannot be added to person", 400)

    return jsonify(PersonDTO(
        profile_url=person_with_pf_paths.profile_url,
        first_name=person_with_pf_paths.first_name,
        last_name=person_with_pf_paths.last_name,
        date_of_birth=person_with_pf_paths.date_of_birth,
        sex=person_with_pf_paths.sex,
        city=person_with_pf_paths.city,
        profile_text=person_with_pf_paths.profile_text,
        pf_path_l=f"{API_URL}/images/large/{person_with_pf_paths.pf_path_l}",
        pf_path_m=f"{API_URL}/images/medium/{person_with_pf_paths.pf_path_m}",
    ).model_dump(mode='json')), 200


@person.route("/search/<string:query>", methods=["GET"])
def search_person(query: str):
    db: Session = next(get_db())

    if query is None:
        return detail_response("Please enter a search query", 400)

    possible_matches = []

    name_parts = query.split()

    if len(name_parts) == 1:
        profile_url_results = search_by_profile_url(db, query)
        if profile_url_results:
            possible_matches.extend(profile_url_results)
    elif len(name_parts) == 2:
        name_results = search_by_first_and_last_name(db, query)
        if name_results:
            possible_matches.extend(name_results)
    else:
        return detail_response("Invalid search query format", 400)

    if not possible_matches:
        return detail_response("No matches found", 400)

    possible_matches_dto = [
        PersonSimpleDTO(
            profile_url=match_person.profile_url,
            first_name=match_person.first_name,
            last_name=match_person.last_name,
            sex=match_person.sex,
            pf_path_m=f"{API_URL}/images/medium/{match_person.pf_path_m}" if match_person.pf_path_m else None,
        ).model_dump(mode='json')
        for match_person in possible_matches]

    return possible_matches_dto, 200