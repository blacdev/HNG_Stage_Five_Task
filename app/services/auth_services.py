import bcrypt
from jose import jwt
from random import randint
import re
import datetime
from app.settings import settings
from app.models.auth_models import User, Auth, Sessions
from sqlalchemy.orm import Session
from app.schemas.auth_schemas import UserSignUp, UserLogin, UserResponse, UserData
from app.Responses.custom_response import CustomResponse, CustomException


def create_account(
    email:str,
    password:str,
    db:Session,
    username:str,
    first_name:str="",
    last_name:str= "",
    phone_number:str = "",
    address:str = "",
    auth_type:str = "local"
) -> CustomResponse:
    
    if auth_type == "local":
        check_email = db.query(User).filter(User.email == email).first()

        if check_email:
            raise CustomException(
                status_code=400,
                message="Email already exists",
            )
        
        check_username = db.query(User).filter(User.username == username).first()

        if check_username:
            raise CustomException(
                status_code=400,
                message="Username already exists",
                
            )
        
        user_instance = User(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            address=address,
            username=username,
            email=email,
            password_hash=hash_password(password)
        )

        try:

            db.add(user_instance)
            db.commit()
            db.refresh(user_instance)

            user_instance.create_auth(db, auth_type)

            return CustomResponse(
                status_code=201,
                message="Account created successfully",
                data=""
            )
        
        except Exception as e:
            print(e)
            return CustomException(
                status_code=500,
                message="failed to create account",
                data=""
            )
    


def user_login(email:str, password:str, db:Session) -> CustomResponse:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise CustomException(
            status_code=400,
            message="User does not exist",
        )
    
    if not compare_password(password, user.password_hash):
        raise CustomException(
            status_code=400,
            message="Incorrect password",
        )
    
    token = generate_token(user.email, user.first_name, user.last_name)


    setattr(user, "token", token)
    return CustomResponse(
        status_code=200,
        message="Login successful",
        data={
            "user":{
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "username": user.username,
                "phone_number": user.phone_number,
                
            },
            "token": token
        }   
    )
def hash_password(password):
    """
    hash_password returns an encrypted version of the password
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def compare_password(password, hashed_password):
    """
    compare_password compares a password with a hashed password.
    It returns True if they match, False otherwise.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_token(email, first_name, last_name):
    # encode secret key with HS256 algorithm

    token = jwt.encode(
        claims={
            "email": email,
            "name": f"{first_name} {last_name}",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=30),
            "iat": datetime.datetime.utcnow(),
            "iss": "merge-cast-api",
            "aud": "merge-cast-app",
        },
        key=settings.SECRET_KEY,
        algorithm="HS256",
    )

    return token


# decode token
def decode_token(token):
    # return jws.verify(token, SECRET_KEY, algorithms=["HS256"])
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=["HS256"],
        audience="merge-cast-app",
        issuer="merge-cast-api",
    )





def generate_verification_code(n: int):
    range_start = 10 ** (n - 1)
    range_end = (10**n) - 1
    return randint(range_start, range_end)