"""
This module contains all the routes for the application

They include:
    - User registration
    - User login via email, password
    - User login via google
    - User logout
    - User profile update
    - User forgot password
    - User password reset
"""
from fastapi import APIRouter, File, UploadFile, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db import get_db
from app.models.auth_models import User, Auth, Sessions
from app.Responses.custom_response import CustomResponse
from app.schemas.auth_schemas import UserSignUp, UserLogin, UserResponse
from app.services.auth_services import create_account, user_login

app = APIRouter()



@app.post("/register")
async def register(
    request: UserSignUp, 
    db: Session = Depends(get_db)
    ) -> CustomResponse:
    
    return create_account(
        **request.model_dump(),
        db=db 
    )


@app.post("/login")
async def login(
    request: UserLogin, 
    db: Session = Depends(get_db)
    ) -> CustomResponse:
    
    return user_login(
        **request.model_dump(),
        db=db
    )


@app.post("/google-login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    ...


@app.post("/logout")
async def logout(request: Request, db: Session = Depends(get_db)):
    ...


@app.post("/update-profile")
async def update_profile(request: Request, db: Session = Depends(get_db)):
    ...


@app.post("/forgot-password")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
    ...


@app.post("/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    ...


