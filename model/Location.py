from database import Base
from sqlalchemy import Column, Integer, VARCHAR, ForeignKey


class Location(Base):
    """ Location information. """
    __tablename__ = 'location'

    location_id = Column("location_id", Integer, primary_key=True, autoincrement=True, nullable=False)
    gym_name = Column("gym_name", VARCHAR(64), nullable=True)
    country = Column(VARCHAR(64), ForeignKey('country.country_name'), nullable=False)
    city = Column("city", VARCHAR(64), nullable=False)
    address = Column("address", VARCHAR(64), nullable=True)
    zip_code = Column("zip_code", VARCHAR(10), nullable=True)
