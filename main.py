from fastapi import FastAPI, Depends, HTTPException, UploadFile,File, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from datetime import datetime
from fastapi.responses import FileResponse
from db import create_database
from sqlalchemy import and_

from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.Flle_app import app as file_app


app = FastAPI(
    title="File Storage API",
    description="This is a simple API that allows you to upload files to a storage",
    version="1.0.0",
    docs_url="/api/v1",
    redoc_url=None,
    openapi_url="/openapi.json",)

create_database()

app.include_router(file_app, prefix="/api/v1")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    uvicorn.run(app= 'main:app', port=0000, reload=True)