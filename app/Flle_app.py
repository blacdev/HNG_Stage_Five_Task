from fastapi import APIRouter, Depends, HTTPException,File, Request, BackgroundTasks
import os

from uuid import uuid4
from datetime import datetime
from fastapi.responses import FileResponse
from app.models import Files, find_file, Chunk_tracker, Progress
from db import get_db
from sqlalchemy.orm import Session
from app.settings import settings
from app.schemas import FileSchema, FileResponseSchema
import python3_gearman as gearman
 


def getUrlFullPath(request: Request, filename: str, bucket_name: str = None):
    hostname = request.headers.get("host")
    request = f"{request.url.scheme}://"
    if hostname == "127.0.0.1:8000":
        hostname = request + hostname
    else:
        hostname = f"https://{hostname}"  

    return f"{hostname}/files/{bucket_name}/{filename}"





app = APIRouter() 

gm_client = gearman.GearmanClient([settings.GEARMAN_HOST + settings.GEARMAN_PORT])




#  check if Base folder exists
if not os.path.exists(settings.FILES_BASE_FOLDER):
    os.mkdir(settings.FILES_BASE_FOLDER)

#  check if chunks folder exists
if not os.path.exists(settings.CHUNK_BASE_FOLDER):
    os.mkdir(settings.CHUNK_BASE_FOLDER)

# function to create an empty video file
def create_empty_file(file_name: str, bucket_name: str):
    # create folder with bucket name
    if not os.path.exists(os.path.join(settings.FILES_BASE_FOLDER, bucket_name)):
        os.mkdir(os.path.join(settings.FILES_BASE_FOLDER, bucket_name))
    try:

        # create empty file
        with open(file_name, "wb") as f:
            f.write(b"")
        return True
    except Exception as e:
        print(e)
        return False
        
    

    

# function to append bytes to a video file
def append_to_file(file_path: str, file_name: str, bytes: bytes):
    with open(os.path.join(file_path, file_name), "ab") as f:
        f.write(bytes)


# endpoint to create a new file
@app.post(
    "/files/{bucket_name}",
    status_code=201,
    response_model=FileResponseSchema,
)
def create_file(
    request: Request,
    bucket_name: str,
    file_name: str,
    file_type: str,
    db: Session = Depends(get_db),
):
    # check if file name already exists
    existing_file = find_file(bucket_name, file_name, db)
    if existing_file:
        raise HTTPException(status_code=409, detail="File already exists")
    
    # create file
    local_file_path = os.path.join(
        os.path.realpath(settings.FILES_BASE_FOLDER),
        bucket_name,
        file_name+"."+file_type,
    )

    # create chunk bucket in chunks folder
    if not os.path.exists(os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name)):
        os.mkdir(os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name))

    common_path = os.path.commonpath(
        (os.path.realpath(settings.FILES_BASE_FOLDER), local_file_path)
    )
    if os.path.realpath(settings.FILES_BASE_FOLDER) != common_path:
        raise HTTPException(
            status_code=403, detail="File reading from unallowed path"
        )
    
    # create empty file
    if not create_empty_file(local_file_path, bucket_name):
        raise HTTPException(status_code=500, detail="Internal server error")
    

    filesize = os.path.getsize(local_file_path)
    url = getUrlFullPath(request, file_name + "." + file_type, bucket_name)
    file = Files(
        id=uuid4().hex,
        filename=file_name + "." + file_type,
        bucketname=bucket_name,
        filesize=filesize,
        url=url,
    )
    db.add(file)
    db.commit()
    db.refresh(file)
    # create progress tracker
    progress_tracker = Progress(
        id=uuid4().hex,
        file_id=file.id,
        progress=0,
    )
    db.add(progress_tracker)
    db.commit()
    db.refresh(progress_tracker)
    return {
        "message": "Empty file created successfully",
        "data": file
    }

# an endpoint that recieves chunks of a file, write them into the folder with the bucket name and and a uuid4. Then it creates a progress tracker for the file
@app.post(
    "/files/{bucket_name}/{file_name}",
    status_code=201,
)
def store_chunk(
    request: Request,
    bucket_name: str,
    file_name: str,
    chunk_number: int,
    background: BackgroundTasks,
    is_last_chunk: bool=False,
    chunk: bytes = File(...),
    db: Session = Depends(get_db),
):
    # check for chunk bucket
    if not os.path.exists(os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name)):
        os.mkdir(os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name))
    
    chunk_name = f"{file_name}_{chunk_number}.webm"
    chunk_path = os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name, chunk_name)
    
    # check if chunk file already exists
    if os.path.exists(chunk_path):
        raise HTTPException(status_code=409, detail="Chunk already exists")
    # create chunk file with chunk name and chunk number as the name of the file
    
    # find file
    existing_file = find_file(bucket_name, file_name, db)

    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")
    # write chunk to chunk file
    with open(chunk_path, "wb") as f:
        f.write(chunk)
    
    # create progress tracker
    progress_tracker = Chunk_tracker(
        id=uuid4().hex,
        file_id=existing_file.id,
        chunk_number=chunk_number,
        chunk_size=len(chunk),
        chunk_name=chunk_name,
        is_last_chunk=is_last_chunk if is_last_chunk else False
    )
    db.add(progress_tracker)
    db.commit()
    db.refresh(progress_tracker)

    data = existing_file.id + " " + bucket_name + " " + file_name


    background.add_task(
        lambda:gm_client.submit_job("process_video", data, background=True), 
        
        )
    
    if is_last_chunk:
        background.add_task(
            lambda: gm_client.submit_job("transcribe", existing_file.id, background=True)
        )
    return {
        "message": "Chunk created successfully",
        "data": progress_tracker
    }


@app.get(
    "/files/{bucket_name}",
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
        local_file_path = os.path.join(
            os.path.realpath(settings.FILES_BASE_FOLDER),
            existing_file.bucketname,
            existing_file.filename,
        )

        common_path = os.path.commonpath(
            (os.path.realpath(settings.FILES_BASE_FOLDER), local_file_path)
        )
        if os.path.realpath(settings.FILES_BASE_FOLDER) != common_path:
            raise HTTPException(
                status_code=403, detail="File reading from unallowed path"
            )

        return FileResponse(local_file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")



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
        local_file_path = os.path.join(
            os.path.realpath(settings.FILES_BASE_FOLDER),
            existing_file.bucketname,
            existing_file.filename,
        )

        common_path = os.path.commonpath(
            (os.path.realpath(settings.FILES_BASE_FOLDER), local_file_path)
        )
        if os.path.realpath(settings.FILES_BASE_FOLDER) != common_path:
            raise HTTPException(
                status_code=403, detail="File reading from unallowed path"
            )

        os.remove(local_file_path)
        db.delete(existing_file)
        db.commit()
        return {"message": "file deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")


#  track progress of file
@app.get("/files/{bucket_name}/{file_name}/progress")
def track_progress(
    bucket_name: str, file_name: str, db: Session = Depends(get_db)
):
    """
    intro-->
            This endpoint tracks the progress of a file. To use this endpoint you need to make a get request to the /files/{bucket_name}/{file_name}/progress endpoint

            paramDesc-->On get request the url takes two query parameters:

                param-->bucket_name: This is the name of the bucket containing the file of interest
                param-->file_name: This is the name of the file of interest

            returnDesc--> On successful request, it returns
                returnBody--> the progress of the file

        Example:
            - Example 1 (Successful Request and Response):
                Request:
                {
                    "bucket_name": "Sample Bucket",
                    "file_name": "Sample File"
                }
                Response (200 OK):
                {
                    "message": "progress retrieved successfully",
                    "data": {
                        "id": "<id>",
                        "file_id": "<file_id>",
                        "progress": "<progress>"
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
        progress = db.query(Progress).filter(Progress.file_id == existing_file.id).first()
        if progress:
            if progress.is_completed:
                return {
                    "message": "progress retrieved successfully",
                    "data": progress
                }
            else:
                return {
                    "message": "progress retrieved successfully",
                    "data": {
                        "id": None,
                        "file_id": file_name,
                        "progress": 0
                    }
                }

        else:
            return {
                "message": "progress retrieved successfully",
                "data": {
                    "id": None,
                    "file_id": file_name,
                    "progress": 0
                }
            }
    else:
        raise HTTPException(status_code=404, detail="File not found")