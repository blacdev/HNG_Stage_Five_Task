from fastapi import FastAPI, Depends, HTTPException, UploadFile,File, Request
import uvicorn
from typing import List
from uuid import uuid4
from datetime import datetime
from fastapi.responses import FileResponse
from models import Files, find_file
from db import get_db, create_database
from sqlalchemy import and_
from sqlalchemy.orm import Session
from settings import settings
from schemas import FileSchema, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cloudinary.uploader



cloudinary.config(
    cloud_name=settings.cloud_name,
    api_key=settings.api_key,
    api_secret=settings.secret_key
)

app = FastAPI(
    prefix="/api/v1",
    title="File Storage API",
    description="This is a simple API that allows you to upload files to a storage",
    version="1.0.0",
    docs_url="/",
    redoc_url=None,
    openapi_url="/openapi.json",
)

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_database()




@app.post("/upload-file/{bucket_name}/", status_code=201, response_model=FileResponse)
async def upload_file(
    request: Request,
    bucket_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
            intro--> This endpoint allows you to upload a file to a bucket/storage. To use this endpoint you need to make a post request to the /upload-file/{bucket_name}/ endpoint

                paramDesc--> 
                        On post request the url takes the query parameter:
                        - bucket_name
                        - file

                    param--> bucket_name: This is the name of the folder you want to upload the file to. It is unique to each user
                    param--> file: This is a boolean value that if set to true renames the hex values

                returnDesc--> 
                        On successful request, it returns

                    returnBody--> details of the file just created

            Example:
                - Example 1 (Successful Request and Response):
                    Request:
                    {
                        "bucket_name": "Sample Bucket",
                        "file": "<file>"
                    }
                    Response (201 Created):
                    {
                        "message": "file uploaded successfully",
                        "data":{
                        "id": "<id>",
                        "filename": "<filename>",
                        "bucketname": "<bucketname>",
                        "date_created": "<date_created>",
                        "last_updated": "<last_updated>",
                        "url": "<url>",
                        "play_back_url": "<play_back_url>"
                        }
                    }
                
                - Example 2 (Invalid Request):
                    Request:
                    {
                        "bucket_name": "Sample Bucket",
                        "file": "<file>"
                    }
                    Response (400 Bad Request):
                    {
                        "detail": [
                            {
                                "loc": [
                                    "body",
                                    "item",
                                    "name"
                                ],
                                "msg": "value is not a valid string",
                                "type": "type_error.str"
                            }
                        ]
                    }

    """

    # Make sure the bucket name does not contain any paths
    if bucket_name.isalnum() == False:
        raise HTTPException(
            status_code=406, detail="Bucket name has to be alpha-numeric"
        )
    old_file_name = file.filename
    file.filename = uuid4().hex
    # Try to write file. Throw exception if anything bad happens
    try:
        data = cloudinary.uploader.upload(file.file, resource_type="video", tags=[bucket_name, old_file_name], public_id=file.filename, folder=bucket_name)
        print(data)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500, detail="Upload Error: ")

    # Check if the file exists
    existing_file = find_file(bucket_name, file.filename, db)
    if existing_file:
        existing_file.last_updated = datetime.utcnow()
        existing_file.url = data['url']
        db.commit()
        db.refresh(existing_file)

        return existing_file 
    else:
        # Create a db entry for this file.
        file = Files(
            id=uuid4().hex,
            filename=file.filename,
            bucketname=bucket_name,
            url=data.get('url', None),
        )
        db.add(file)
        db.commit()
        db.refresh(file)

        data = {
            "message": "file uploaded successfully",
            "data":{
            "id": file.id,
            "filename": file.filename,
            "bucketname": file.bucketname,
            "date_created": file.date_created,
            "last_updated": file.last_updated,
            "url": file.url,
            "play_back_url": data.get("playback_url", None)
            }
        }

        return data
    

@app.get("/files/{bucket_name}/{file_name}", status_code=200)
def get_file(
    bucket_name: str, file_name: str, db: Session = Depends(get_db)
):

    """
    intro-->
            This endpoint returns a single file from the storage. To use this endpoint you need to make a get request to the /files/{bucket_name}/{file_name} endpoint

            paramDesc-->On get request the url takes two query parameters:

                param-->bucket_name: This is the name of the bucket containing the file of interest
                param-->file_name: This is the name of the file of interest

            returnDesc--> On successful request, it returns
                returnBody--> details of the file of interest

        Example:
            - Example 1 (Successful Request and Response):
                Request:
                {
                    "bucket_name": "Sample Bucket",
                    "file_name": "Sample File"
                }
                Response (200 OK):
                {
                    "message": "file info retrieved successfully",
                    "data":{
                    "id": "<id>",
                    "filename": "<filename>",
                    "bucketname": "<bucketname>",
                    "date_created": "<date_created>",
                    "last_updated": "<last_updated>",
                    "url": "<url>"
                    }
                }
            
            - Example 2 (Invalid Request):
                Request:
                {
                    "bucket_name": "Sample Bucket",
                    "file_name": "Sample File"
                }
                Response (404 Not Found):
                {
                    "detail": "File not found"
                }


    """
    existing_file = find_file(bucket_name, file_name, db)
    if existing_file:
        data = {
            "message": "file info retrieved successfully",
            "data":{
            "id": existing_file.id,
            "filename": existing_file.filename,
            "bucketname": existing_file.bucketname,
            "date_created": existing_file.date_created,
            "last_updated": existing_file.last_updated,
            "url": existing_file.url
            }
        }

        return data
    else:
        raise HTTPException(status_code=404, detail="File not found")



@app.get(
    "/files/{bucket_name}/",
    response_model=List[FileSchema]
)
def get_all_files(request:Request, bucket_name: str, db: Session = Depends(get_db)):
    """
    intro-->
            This endpoint returns all files from the storage. To use this endpoint you need to make a get request to the /files/{bucket_name}/ endpoint

            paramDesc-->On get request the url takes one query parameter:
                
                    param-->bucket_name: This is the name of the bucket containing the file of interest

            returnDesc--> On successful request, it returns
                returnBody--> details of all the files in the bucket

        Example:
            - Example 1 (Successful Request and Response):
                Request:
                {
                    "bucket_name": "Sample Bucket"
                }
                Response (200 OK):
                {
                    "message": "files retrieved successfully",
                    "data": [
                        {
                            "id": "<id>",
                            "filename": "<filename>",
                            "bucketname": "<bucketname>",
                            "date_created": "<date_created>",
                            "last_updated": "<last_updated>",
                            "url": "<url>"
                        },
                        {
                            "id": "<id>",
                            "filename": "<filename>",
                            "bucketname": "<bucketname>",
                            "date_created": "<date_created>",
                            "last_updated": "<last_updated>",
                            "url": "<url>"
                        }
                    ]
                }
            
            - Example 2 (Invalid Request):
                Request:
                {
                    "bucket_name": "Sample Bucket"
                }
                Response (404 Not Found):
                {
                    "detail": "Bucket not found"
                }
    """
    files = db.query(Files).filter(Files.bucketname == bucket_name).all()
    if not files:
        raise HTTPException(status_code=404, detail="Bucket not found")
    return {
        "message": "files retrieved successfully",
        "data": files
    }






# delete file
@app.delete("/files/{bucket_name}/{file_name}")
def delete_file(
    bucket_name: str, file_name: str, db: Session = Depends(get_db)
):
    """
    intro-->
            This endpoint deletes a single file from the storage. To use this endpoint you need to make a delete request to the /files/{bucket_name}/{file_name} endpoint

            paramDesc-->On delete request the url takes two query parameters:

                param-->bucket_name: This is the name of the bucket containing the file of interest
                param-->file_name: This is the name of the file of interest

            returnDesc--> On successful request, it returns
                returnBody--> a message confirming the deletion of the file

        Example:
            - Example 1 (Successful Request and Response):
                Request:
                {
                    "bucket_name": "Sample Bucket",
                    "file_name": "Sample File"
                }
                Response (200 OK):
                {
                    "message": "file deleted successfully"
                }
            
            - Example 2 (Invalid Request):
                Request:
                {
                    "bucket_name": "Sample Bucket",
                    "file_name": "Sample File"
                }
                Response (404 Not Found):
                {
                    "detail": "File not found"
                }
    """

    existing_file = find_file(bucket_name, file_name, db)
    if existing_file:
        try:
            cloudinary.uploader.destroy(existing_file.filename, resource_type="video")
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=500, detail="Could not delete file ")

        db.delete(existing_file)
        db.commit()
        return {
            "message": "file deleted successfully"
            }
    else:
        raise HTTPException(status_code=404, detail="File not found")




if __name__ == "__main__":
    uvicorn.run(app= 'main:app', port=8000, reload=True)