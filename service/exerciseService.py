import logging
from datetime import datetime
from typing import List

from flask import abort
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from dto.exerciseDTO import ExerciseDTO
from model.Exercise import Exercise
from model.GymaExercise import GymaExercise


def get_exercise_by_exercise_id(db: Session, exercise_id: int) -> Exercise | None:
    """ Get Exercise object by exercise id from database. """
    try:
        result = db.execute(select(Exercise).filter_by(exercise_id=exercise_id))
        exercise = result.scalar_one_or_none()
        return exercise
    except NoResultFound:
        return None


def get_exercises_by_gyma_id(db: Session, gyma_id: int) -> List[Exercise] | None:
    """ Get list of Exercise objects by gyma id from database. """
    try:
        result = db.execute(select(Exercise).filter_by(gyma_id=gyma_id))
        exercises = result.scalars().all()
        return list(exercises)
    except NoResultFound:
        return None


def add_exercise_db(db: Session, gyma_id: int, exercise_dto: ExerciseDTO) -> int | None:
    """ Add a new exercise to a Gyma and create a record in GymaExercise table. """
    try:
        new_exercise = Exercise(
            exercise_name=exercise_dto.exercise_name,
            exercise_type=exercise_dto.exercise_type,
            count=exercise_dto.count,
            sets=exercise_dto.sets,
            weight=exercise_dto.weight,
            minutes=exercise_dto.minutes,
            km=exercise_dto.km,
            level=exercise_dto.level,
            description=exercise_dto.description,
            created_at=datetime.now()
        )
        db.add(new_exercise)
        db.commit()
        db.refresh(new_exercise)

        gyma_exercise = GymaExercise(gyma_id=gyma_id, exercise_id=new_exercise.exercise_id)
        db.add(gyma_exercise)
        db.commit()

        if gyma_exercise and new_exercise:
            return new_exercise.exercise_id

        return None
    except SQLAlchemyError as e:
        logging.error(f"Error adding exercise to gyma: {e}")
        db.rollback()
        return None


def remove_exercise_by_gyma_and_id(db: Session, gyma_id: int, exercise_id: int) -> bool:
    """ Remove an Exercise and its related GymaExercise from the database based on gyma_id and exercise details. """
    try:
        exercise_query = (
            select(Exercise)
            .join(GymaExercise, GymaExercise.exercise_id == Exercise.exercise_id)
            .filter(GymaExercise.gyma_id == gyma_id)
            .filter(Exercise.exercise_id == exercise_id)
        )

        exercise = db.execute(exercise_query).scalar_one_or_none()

        if exercise is None:
            logging.error("Exercise not found")
            return False

        gyma_exercise_query = (
            select(GymaExercise)
            .filter(GymaExercise.gyma_id == gyma_id, GymaExercise.exercise_id == exercise.exercise_id)
        )

        gyma_exercise = db.execute(gyma_exercise_query).scalar_one_or_none()

        db.delete(gyma_exercise)
        db.delete(exercise)

        db.commit()
        return True

    except SQLAlchemyError as e:
        logging.error(f"Error removing exercise and its related gyma_exercise: {e}")
        db.rollback()
        return False
    except Exception as e:
        logging.error(f"Exception: Error removing exercise: {e}")
        db.rollback()
        return False
