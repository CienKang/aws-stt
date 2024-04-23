from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base  = declarative_base()
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True , autoincrement=True)
    filename = Column(String)
    s3_url = Column(String)
    type = Column(String)
    is_processed = Column(Boolean)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)