from sqlalchemy.orm import relationship

from database import Base
from sqlalchemy import Column, Integer, VARCHAR, Enum, DateTime, Float, ForeignKey


class Exercise(Base):
    """ Characteristics of a gym exercise. """
    __tablename__ = 'exercise'

    exercise_id = Column("exercise_id", Integer, primary_key=True, autoincrement=True)
    exercise_name = Column("exercise_name", VARCHAR(64), nullable=False)
    exercise_type = Column("exercise_type", Enum('gains', 'cardio', 'other'), nullable=False)
    count = Column("count", Integer, nullable=True)
    sets = Column("sets", Integer, nullable=True)
    weight = Column("weight", Float, nullable=True)
    minutes = Column("minutes", Integer, nullable=True)
    km = Column("km", Float, nullable=True)
    level = Column("level", Integer, nullable=True)
    description = Column("description", VARCHAR(64), nullable=True)
    created_at = Column("created_at", DateTime, nullable=False)

    gymas = relationship("GymaExercise", back_populates="exercise")
