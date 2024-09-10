from sqlalchemy import Column, Integer, ForeignKey, Enum, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
from model.Person import Person


class Friendship(Base):
    __tablename__ = 'friendship'

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('person.person_id'), nullable=False)
    friend_id = Column(Integer, ForeignKey('person.person_id'), nullable=False)
    status = Column(Enum('pending', 'accepted', 'blocked'), nullable=False, default='pending')
    since = Column(Date, nullable=False)

    person = relationship(
        'Person',
        foreign_keys=[person_id, friend_id],
        back_populates='friends',
        primaryjoin='Friendship.person_id == Person.person_id',
        overlaps="friends"
    )

    friend = relationship(
        'Person',
        foreign_keys=[friend_id],
        primaryjoin='Friendship.friend_id == Person.person_id',
        overlaps="friends"
    )

    __table_args__ = (UniqueConstraint('person_id', 'friend_id', name='_person_friend_uc'),)
