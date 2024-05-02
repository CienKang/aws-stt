from datetime import datetime
from sqlalchemy.orm import Session
from postgres.config import SessionLocal
from postgres.models import File

db = SessionLocal()


def get_files(skip: int = 0, limit: int = 100):
    return db.query(File).offset(skip).limit(limit).all()

def get_file_by_id(file_id: str):
    return db.query(File).filter(File.id == file_id).first()

def create_file(filename: str, s3_url: str, type: str, is_processed: bool):
    db_file = File(
        filename=filename, 
        s3_url=s3_url, 
        type=type, 
        is_processed=is_processed, 
        created_at=datetime.now(), 
        updated_at=datetime.now()
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def update_file_status(filename: str, is_processed: bool):
    db_file = db.query(File).filter(File.filename == filename).first()
    print(filename)
    db_file.is_processed = is_processed
    db_file.updated_at = datetime.now()
    db.commit()
    db.refresh(db_file)
    return db_file

def delete_file(id: int):
    db_file = db.query(File).filter(File.id == id).first()
    if db_file:
        db.delete(db_file)
        db.commit()
    else :
        return None
    
    return db_file