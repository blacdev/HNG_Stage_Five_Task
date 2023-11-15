import uvicorn
from fastapi import FastAPI, APIRouter
from db import create_database
from app.settings import settings
from fastapi.middleware.cors import CORSMiddleware

########## include app routers here ##########

from app.routers.v1_router import app as v1_app
#############################################

# create base folders
settings.create_base_folders()

app = FastAPI(
    title="File Storage API",
    description="This is a simple API that allows you to upload files to a storage",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/openapi.json",)

# create database
create_database()

# include app routers here
app.include_router(
    v1_app,
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    uvicorn.run(app= 'main:app', port=8000, reload=True, )