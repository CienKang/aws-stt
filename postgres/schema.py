import datetime
from pydantic import BaseModel

class File(BaseModel):
    id: str
    filename: str
    s3_url: str
    type: str
    is_processed: bool
    created_at: datetime

    class Config:
        orm_mode = True