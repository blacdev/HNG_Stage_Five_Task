from fastapi import APIRouter, Depends, HTTPException,File, Request, BackgroundTasks
import os
from uuid import uuid4
from fastapi.responses import StreamingResponse
from app.models import Files, find_file, Blob_tracker, Progress
from db import get_db
from sqlalchemy.orm import Session
from app.settings import settings
from app.schemas import FileResponseSchema
from app.services import getUrlFullPath, create_empty_file, video_streamer
from app.blob_processor import video_processing_start



app = APIRouter() 


# endpoint to create a new file
@app.post(
    "/files",
    status_code=201,
    response_model=FileResponseSchema,
)
def create_file(
    request: Request,
    file_name: str,
    file_type: str,
    db: Session = Depends(get_db),
):
    
    bucket_name = uuid4().hex

    # check if file name already exists
    existing_file = find_file(bucket_name, file_name, db)
    if existing_file:
        raise HTTPException(status_code=409, detail=f"File with this name({file_name+ '.' + file_type}) already exists")
    
    # create file
    local_file_path = os.path.join(
        os.path.realpath(settings.FILES_BASE_FOLDER),
        bucket_name,
        file_name+"."+file_type,
    )

    # create blob bucket in blob folder
    if not os.path.exists(os.path.join(settings.BLOB_BASE_FOLDER, bucket_name)):
        os.mkdir(os.path.join(settings.BLOB_BASE_FOLDER, bucket_name))

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
    
    id=uuid4().hex
    print(id)
    file = Files(
        id = id,
        filename=file_name + "." + file_type,
        bucketname=bucket_name,
        filesize=filesize,
        url=getUrlFullPath(request, file_id=id),
    )

    db.add(file)
    db.commit()
    db.refresh(file)

    # create progress tracker
    progress_tracker = Progress(
        id=uuid4().hex,
        file_id=file.id,
        progress_position=0,
        expected_progress_count=0,
        is_completed=False
    )

    db.add(progress_tracker)
    db.commit()
    db.refresh(progress_tracker)
    return {
        "message": "Empty file created successfully",
        "data": file
    }


@app.post(
    "/files/{file_id}",
    status_code=201,
)
def store_blob(
    file_id: str,
    blob_sequnece: int,
    background: BackgroundTasks,
    is_last_blob: bool=False,
    blob: bytes = File(...),
    db: Session = Depends(get_db),
):
    file = db.query(Files).filter(Files.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # check for blob bucket
    if not os.path.exists(os.path.join(settings.BLOB_BASE_FOLDER, file.bucketname)):
        os.mkdir(os.path.join(settings.BLOB_BASE_FOLDER, file.bucketname))
    
    blob_name =  f"{file.filename.split('.')[0]}_{blob_sequnece}.{file.filename.split('.')[1]}"
    blob_path = os.path.join(settings.BLOB_BASE_FOLDER, file.bucketname, blob_name)
    

    # write blob to blob file
    try:
        with open(blob_path, "wb") as f:
            f.write(blob)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="failed to save blob to bucket")
    
    # create progress tracker
    progress_tracker = Blob_tracker(
        id=uuid4().hex,
        file_id=file.id,
        blob_sequnce=blob_sequnece,
        blob_size=len(blob),
        blob_name=blob_name,
        is_last_blob=is_last_blob if is_last_blob else False
    )
    db.add(progress_tracker)
    db.commit()
    db.refresh(progress_tracker)
    
    #TODO: create a background task to process the blobs when the last blob is recieved
    background.add_task(
        video_processing_start,
        file_id=file.id
    )

    return {
        "message": "blob created successfully",
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
    return {
        "message": "files retrieved successfully",
        "data": files if len(files) > 0 else []
    }


@app.get("/files/{file_id}", status_code=200)   
def get_file(
    file_id: str, db: Session = Depends(get_db)
):
    file = db.query(Files).filter(Files.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
        
    return {
            "message": "file info retrieved successfully",
            "data": file
        }
    

@app.get("/files/stream/{file_id}", status_code=200)
def stream_file(
    file_id: str, db: Session = Depends(get_db)
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
    existing_file = db.query(Files).filter(Files.id == file_id).first()
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

        
        StreamingResponse(video_streamer(local_file_path), status_code=200, media_type="video/webm")
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
@app.get("/files/progress/{file_id}")
def track_progress(
    file_id: str, db: Session = Depends(get_db)
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
    

    progress = db.query(Progress).filter(Progress.file_id == file_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "message": "progress retrieved successfully",
        "data": progress if progress else {}
    }