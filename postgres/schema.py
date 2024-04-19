from pydantic import BaseModel

class User(BaseModel):
    id: str
    username: str
    fmno: int
    hashedPassword: str


    class Config:
        orm_mode = True