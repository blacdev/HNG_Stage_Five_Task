from fastapi import APIRouter


from app.routers.File_app import app as file_app
from app.routers.auth import app as auth_app

app = APIRouter(
    prefix="/api/v1",
)

app.include_router(auth_app, tags=["auth v1"],)
app.include_router(file_app, tags=["File Storage v1"],)