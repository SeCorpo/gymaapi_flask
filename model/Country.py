from database import Base
from sqlalchemy import Column, VARCHAR, Enum, EnumType


class Continent(Enum):
    africa = "Africa"
    antarctica = "Antarctica"
    asia = "Asia"
    europe = "Europe"
    north_america = "North America"
    south_america = "South America"
    oceania = "Oceania"


class Country(Base):
    """ List of countries. """
    __tablename__ = 'country'

    country_name = Column("country_name", VARCHAR(64), primary_key=True)
    continent = Column(EnumType(Continent))
