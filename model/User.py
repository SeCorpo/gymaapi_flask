from database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, VARCHAR, Enum, Boolean, LargeBinary


class User(Base):
    """ User account, only for authentication. """
    __tablename__ = 'user'

    user_id = Column("user_id", Integer, primary_key=True, autoincrement=True, nullable=False)
    email = Column("email", VARCHAR(length=255), unique=True, nullable=False, index=True)
    password_hash = Column("password_hash", LargeBinary(length=60), nullable=False)
    salt = Column("salt", LargeBinary(length=16), nullable=False)
    account_type = Column("account_type", Enum("admin", "user"), nullable=False, default="user")
    email_verified = Column("email_verified", Boolean, default=False, nullable=False)
