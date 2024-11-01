from typing import List, Optional

from pydantic import BaseModel

from dto.gymaDTO import GymaDTO
from dto.personDTO import PersonDTO, PersonSimpleDTO


class ProfileDTO(BaseModel):
    personDTO: PersonDTO
    gyma_list: List[GymaDTO] = []
    friend_list: List[PersonSimpleDTO] = []
    friendship_status: Optional[str] = None


class MyProfileDTO(BaseModel):
    personDTO: PersonDTO
    gyma_list: List[GymaDTO] = []
    friend_list: List[PersonSimpleDTO] = []
    pending_friend_list: List[PersonSimpleDTO] = []
    blocked_friend_list: List[PersonSimpleDTO] = []

class MyProfileUpdateListsDTO(BaseModel):
    friend_list: List[PersonSimpleDTO] = []
    pending_friend_list: List[PersonSimpleDTO] = []
    blocked_friend_list: List[PersonSimpleDTO] = []