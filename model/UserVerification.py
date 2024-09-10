from database import Base
from sqlalchemy import Column, VARCHAR, Integer, ForeignKey


class UserVerification(Base):
    """ Email verification codes with accompanying user_id. """
    __tablename__ = 'user_verification'

    user_id = Column(Integer, ForeignKey('user.user_id'), primary_key=True, nullable=False, index=True)
    verification_code = Column(VARCHAR(length=64), nullable=False)
