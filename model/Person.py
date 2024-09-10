from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, VARCHAR, Enum, Date, ForeignKey, Text


class Person(Base):
    """ Personal information of users, including settings. """
    __tablename__ = 'person'

    person_id = Column(Integer, ForeignKey('user.user_id'), primary_key=True, nullable=False, index=True)
    profile_url = Column("profile_url", VARCHAR(length=32), nullable=False, index=True, unique=True)
    first_name = Column("first_name", VARCHAR(64), nullable=False)
    last_name = Column("last_name", VARCHAR(64), nullable=False)
    date_of_birth = Column("date_of_birth", Date, nullable=False)
    sex = Column("sex", Enum('m', 'f', 'o'), nullable=False)
    # country = Column(VARCHAR(64), ForeignKey('country.country_name'), nullable=False)
    city = Column("city", VARCHAR(64), nullable=True)
    profile_text = Column("profile_text", Text, nullable=True)
    gyma_share = Column("gyma_share", Enum("solo", "gymbros", "pub"), nullable=False, default="pub")

    pf_path_m = Column("pf_path_m", VARCHAR(64), nullable=True)
    pf_path_l = Column("pf_path_l", VARCHAR(64), nullable=True)

    friends = relationship(
        'Friendship',
        primaryjoin='or_(Person.person_id == Friendship.person_id, Person.person_id == Friendship.friend_id)',
        back_populates='person',
        overlaps="person,friends"
    )
