from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class User(BaseModel):
  email: EmailStr


class UserSignUp(User):
  username: str
  first_name: Optional[str] = None
  last_name: Optional[str] = None
  password: str
  phone_number: Optional[str] = None
  address: Optional[str] = None
  auth_type: Optional[str] = "local"


class UserLogin(User):
  password: str

class UserData(UserSignUp):
  id: str

  class config:
    orm_mode = True
    include = ("id")
    exclude = ('password',"type")

class UserResponse(BaseModel):
  ...