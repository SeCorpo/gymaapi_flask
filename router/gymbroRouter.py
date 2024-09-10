import logging
from flask import Blueprint, request, jsonify, abort
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dto.exerciseDTO import ExerciseDTO
from dto.gymaDTO import GymaDTO
from dto.personDTO import PersonSimpleDTO
from provider.authProvider import get_auth_key
from provider.gymbroProvider import get_last_ten_gyma_entries_of_user_and_friends
from service.personService import get_person_by_user_id
from session.sessionService import get_user_id_from_session_data

gymbro = Blueprint('gymbro', __name__, url_prefix='/api/v1/gymbro')

@gymbro.route("", methods=['GET'])
def get_gymbro_ten_latest():
    db: Session = next(get_db())
    auth_token = get_auth_key()
    gyma_keys = request.headers.get('Gymakeys', None)

    logging.info(f"Searching for the latest ten gyma entries {'excluding: ' + gyma_keys if gyma_keys else ''}")

    user_id = get_user_id_from_session_data(auth_token)
    if user_id is None:
        abort(401, description="Session invalid")

    gymbro_ten_latest_gyma = get_last_ten_gyma_entries_of_user_and_friends(db, user_id, gyma_keys)

    gymbro_gyma_with_exercises = []
    for gyma in gymbro_ten_latest_gyma:
        person_of_gyma = get_person_by_user_id(db, gyma.user_id)

        person_simple_dto = PersonSimpleDTO(
            profile_url=person_of_gyma.profile_url,
            first_name=person_of_gyma.first_name,
            last_name=person_of_gyma.last_name,
            sex=person_of_gyma.sex,
            pf_path_m=person_of_gyma.pf_path_m,
        ).model_dump(mode='json')

        exercise_dtos = [
            ExerciseDTO(
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

        gymbro_gyma_with_exercises.append(gyma_dto)

    return jsonify(gymbro_gyma_with_exercises), 200
