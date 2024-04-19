from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base  = declarative_base()
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True )
    username = Column(String, unique=True )
    fmno = Column(Integer, unique=True )
    hashedPassword = Column(String)
