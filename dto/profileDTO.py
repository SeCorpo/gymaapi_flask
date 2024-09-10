from typing import List, Optional

from pydantic import BaseModel

from dto.personDTO import PersonDTO, PersonSimpleDTO


class ProfileDTO(BaseModel):
    personDTO: PersonDTO
    friend_list: List[PersonSimpleDTO] = []
    friendship_status: Optional[str] = None


class MyProfileDTO(BaseModel):
    personDTO: PersonDTO
    friend_list: List[PersonSimpleDTO] = []
    pending_friend_list: List[PersonSimpleDTO] = []
