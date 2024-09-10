from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class GymaExercise(Base):
    __tablename__ = 'gyma_exercise'

    id = Column(Integer, primary_key=True, autoincrement=True)
    gyma_id = Column(Integer, ForeignKey('gyma.gyma_id'), nullable=False, index=True)
    exercise_id = Column(Integer, ForeignKey('exercise.exercise_id'), nullable=False, index=True)

    gyma = relationship("Gyma", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="gymas")
