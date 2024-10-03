from pydantic import BaseModel, Field


class ExerciseDTO(BaseModel):
    exercise_id: int = Field(default=None)
    exercise_name: str
    exercise_type: str
    count: int | None = Field(default=None)
    sets: int | None = Field(default=None)
    weight: float | None = Field(default=None)
    minutes: int | None = Field(default=None)
    km: float | None = Field(default=None)
    level: int | None = Field(default=None)
    description: str | None = Field(default=None)
