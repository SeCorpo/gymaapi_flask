from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from dto.exerciseDTO import ExerciseDTO
from dto.personDTO import PersonSimpleDTO


class GymaDTO(BaseModel):
    gyma_id: int = Field(..., description="Used for excluding gyma to send, when client has them in localstorage")
    person: Optional[PersonSimpleDTO] = None
    time_of_arrival: datetime
    time_of_leaving: Optional[datetime] = None
    exercises: List[ExerciseDTO] = []

    model_config = ConfigDict(from_attributes=True)
