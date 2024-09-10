import logging
import os
from flask import Blueprint, request, abort, jsonify
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from dto.imageDTO import ImageDTO
from dto.personDTO import PersonDTO, EnterPersonDTO
from dto.profileDTO import MyProfileDTO
from provider.authProvider import get_auth_key
from provider.imageProvider import process_image, move_images_to_archive
from service.personService import add_person, get_person_by_user_id, edit_person, set_pf_paths
from session.sessionService import get_user_id_from_session_data

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
        abort(400, description="Invalid data format")

    logging.info("Creating or editing person object for user")

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    person_obj = get_person_by_user_id(db, user_id)
    if person_obj is None:
        logging.info("Creating person object for user")
        new_person = add_person(db, user_id, enter_person_dto)
        if new_person is None:
            abort(500, description="Person cannot be created")
        else:
            person_dto = PersonDTO(
                profile_url=new_person.profile_url,
                first_name=new_person.first_name,
                last_name=new_person.last_name,
                date_of_birth=new_person.date_of_birth,
                sex=new_person.sex,
                city=new_person.city,
                profile_text=new_person.profile_text,
                pf_path_l=new_person.pf_path_l,
                pf_path_m=new_person.pf_path_m,
            ).model_dump(mode='json')
            my_profile_dto = MyProfileDTO(
                personDTO=person_dto,
                friend_list=None,
                pending_friend_list=None
            ).model_dump(mode='json')
            return jsonify(my_profile_dto), 200
    else:
        logging.info("Updating person object for user")
        edited_person = edit_person(db, user_id, person_obj, enter_person_dto)
        if edited_person is None:
            abort(500, description="Person cannot be updated")
        else:
            person_dto = PersonDTO(
                profile_url=edited_person.profile_url,
                first_name=edited_person.first_name,
                last_name=edited_person.last_name,
                date_of_birth=edited_person.date_of_birth,
                sex=edited_person.sex,
                city=edited_person.city,
                profile_text=edited_person.profile_text,
                pf_path_l=edited_person.pf_path_l,
                pf_path_m=edited_person.pf_path_m,
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
        abort(400, description="No file provided")

    logging.info("Processing picture for user")

    try:
        image_dto = ImageDTO(file=file)
        image_dto.validate_file(file)  # Perform validation
    except ValueError as e:
        abort(400, description=str(e))

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    person_obj = get_person_by_user_id(db, user_id)
    if person_obj is None:
        abort(404, description="Picture cannot be added if there is no person")

    if person_obj.pf_path_l and person_obj.pf_path_m is not None:
        logging.info("Archiving previous picture of user")
        move_ok = move_images_to_archive(person_obj.pf_path_l, person_obj.pf_path_m)
        if not move_ok:
            abort(500, description="Picture cannot be moved to archive")

    picture_names = process_image(image_dto)
    if picture_names is None:
        abort(500, description="Picture cannot be processed, please try a different picture")

    person_with_pf_paths = set_pf_paths(db, person_obj, picture_names["pf_path_l"], picture_names["pf_path_m"])
    if not person_with_pf_paths:
        abort(500, description="New pictures cannot be added to person")

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
    ).model_dump(mode='json')
    ), 200
