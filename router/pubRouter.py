import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from dto.exerciseDTO import ExerciseDTO
from dto.gymaDTO import GymaDTO
from provider.pubProvider import get_last_ten_gyma_entry

pub = Blueprint('pub', __name__, url_prefix='/api/v1/pub')


@pub.route("", methods=["GET"])
def get_pub_ten_latest():
    db: Session = next(get_db())
    gyma_keys = request.headers.get('Gymakeys', None)

    logging.info(f"Searching for the latest ten gyma entries {'excluding: ' + gyma_keys if gyma_keys is not None else ''}")

    pub_ten_latest_gyma = get_last_ten_gyma_entry(db, gyma_keys)

    pub_gyma_with_exercises = []
    for gyma in pub_ten_latest_gyma:
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
            person=None,  # Replace with a PersonDTO object if needed
            time_of_arrival=gyma.time_of_arrival,
            time_of_leaving=gyma.time_of_leaving,
            exercises=exercise_dtos
        ).model_dump(mode='json')

        pub_gyma_with_exercises.append(gyma_dto)

    return jsonify(pub_gyma_with_exercises), 200
