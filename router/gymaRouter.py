import os

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from database import get_db
from dto.exerciseDTO import ExerciseDTO
from dto.gymaDTO import GymaDTO
from dto.personDTO import PersonSimpleDTO
from provider.authProvider import get_auth_key
from service.exerciseService import add_exercise_db
from service.personService import get_person_by_user_id
from session.sessionService import get_user_id_from_session_data, set_gyma_id_in_session, get_session_data, delete_gyma_id_from_session
from service.gymaService import add_gyma, set_time_of_leaving, get_gyma_by_gyma_id
from util.response import detail_response

API_URL = os.getenv("API_BASE_URL")
gyma = Blueprint('gyma', __name__, url_prefix='/api/v1/gyma')

@gyma.route("/start", methods=['POST'])
def start_gyma():
    db: Session = next(get_db())
    auth_token = get_auth_key()

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        return detail_response("Session invalid", 401)

    person_of_gyma = get_person_by_user_id(db, user_id)

    gyma_instance = add_gyma(db, user_id)
    if gyma_instance is None:
        return detail_response("Gyma cannot be added", 404)

    if set_gyma_id_in_session(auth_token, gyma_instance.gyma_id):
        person_simple_dto = PersonSimpleDTO(
            profile_url=person_of_gyma.profile_url,
            first_name=person_of_gyma.first_name,
            last_name=person_of_gyma.last_name,
            sex=person_of_gyma.sex,
            pf_path_m=f"{API_URL}/images/medium/{person_of_gyma.pf_path_m}" if person_of_gyma.pf_path_m else None,
        )

        gyma_dto = GymaDTO(
            gyma_id=gyma_instance.gyma_id,
            person=person_simple_dto,
            time_of_arrival=gyma_instance.time_of_arrival,
            time_of_leaving=None,
            exercises=[]
        ).model_dump(mode='json')
        return gyma_dto, 201
    else:
        return detail_response("Gyma cannot be set in session", 404)


@gyma.route("/end", methods=['PUT'])
def end_gyma():
    db: Session = next(get_db())
    auth_token = get_auth_key()

    session_data = get_session_data(auth_token)
    if session_data is None or session_data.gyma_id is None or session_data.user_id is None:
        return detail_response("Session invalid", 401)

    gyma_instance = get_gyma_by_gyma_id(db, session_data.gyma_id)
    if gyma_instance is None:
        return detail_response("Gyma does not exist in database", 404)

    time_of_leaving = set_time_of_leaving(db, session_data.user_id, gyma_instance)
    if time_of_leaving is None:
        return detail_response("Failed to set time of leave", 400)

    if delete_gyma_id_from_session(auth_token):
        return {"time_of_leaving": time_of_leaving.isoformat()}, 200
    else:
        return detail_response("Gyma cannot be removed from session", 400)


@gyma.route("/exercise", methods=['POST'])
def add_exercise_to_gyma():
    db: Session = next(get_db())
    auth_token = get_auth_key()

    session_data = get_session_data(auth_token)
    if session_data is None or session_data.gyma_id is None:
        return detail_response("Session invalid", 401)

    exercise_dto = request.json
    exercise_data = ExerciseDTO(**exercise_dto)

    added_exercise = add_exercise_db(db, session_data.gyma_id, exercise_data)
    if added_exercise:
        return jsonify(added_exercise), 201
    else:
        return detail_response("Failed to add exercise", 400)
