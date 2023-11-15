from fastapi import APIRouter, Depends, HTTPException,File, Request, BackgroundTasks
import os
from uuid import uuid4
from fastapi.responses import StreamingResponse, FileResponse
from app.models.file_models import Files, find_file
from db import get_db
from sqlalchemy.orm import Session
from app.settings import settings
from app.schemas.file_schemas import FileResponseSchema
from app.services.file_services import getUrlFullPath, video_streamer
from app.blob_processor import video_processing_start

FILE_FOLDER, BLOB_FOLDER, THUMBNAIL_FOLDER, COMPRESSION_FOLDER = settings.create_base_folders()

app = APIRouter() 

# endpoint to create a new file
@app.post(
    "/files",
    status_code=201,
)
def create_file(
    request: Request,
    file_name: str,
    file_type: str,
    db: Session = Depends(get_db),
):
    
    # TODO: Fix issue with creating multple buckets for the same user 
    bucket_name = uuid4().hex

    # check if file name already exists
    existing_file = find_file(bucket_name, file_name, db)
    if existing_file:
        raise HTTPException(status_code=409, detail=f"File with this name({file_name+ '.' + file_type}) already exists")
    
    id=uuid4().hex

    file = Files(
        id = id,
        filename=file_name + "." + file_type,
        bucket_name=bucket_name,
        filesize=0,
        compressed_filesize=0,
        thumbnail_name = file_name + ".jpg",
        play_back_url=getUrlFullPath(request, file_id=id, type="playback"),
        thumbnail_url=getUrlFullPath(request, file_id=id, type="thumbnail"),
        download_url=getUrlFullPath(request, file_id=id, type="video"),
    )

    db.add(file)
    db.commit()
    db.refresh(file)

    F = [FILE_FOLDER,BLOB_FOLDER, THUMBNAIL_FOLDER, COMPRESSION_FOLDER]

    for folder in F:
        if not os.path.exists(os.path.join(folder, bucket_name)):
            os.mkdir(os.path.join(folder, bucket_name))

    return FileResponseSchema(
        message="file created successfully",
        data=file
    )


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
    if not os.path.exists(os.path.join(BLOB_FOLDER, file.bucket_name)):
        os.mkdir(os.path.join(BLOB_FOLDER, file.bucket_name))
    
    blob_name =  f"{file.filename.split('.')[0]}_{blob_sequnece}.{file.filename.split('.')[1]}"
    blob_path = os.path.join(BLOB_FOLDER, file.bucket_name, blob_name)

    # check if blob with same name already exists
    if os.path.exists(blob_path):
        raise HTTPException(status_code=409, detail=f"Blob with this name({blob_name}) already exists")
    

    # write blob to blob file
    try:
        with open(blob_path, "wb") as bp:
            bp.write(blob)

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="failed to save blob to bucket")
    
    #TODO: create a background task to process the blobs when the last blob is recieved
    if is_last_blob:
        background.add_task(
            video_processing_start,
            file_id=file.id
        )

    return {
        "message": "blob created successfully"
    }


@app.get(
    "/files/{bucket_name}/all",
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
                            "bucket_name": "<bucket_name>",
                            "date_created": "<date_created>",
                            "last_updated": "<last_updated>",
                            "url": "<url>"
                        },
                        {
                            "id": "<id>",
                            "filename": "<filename>",
                            "bucket_name": "<bucket_name>",
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
    files = db.query(Files).filter(Files.bucket_name == bucket_name).all()
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
    


@app.get("/files/{file_id}/download", status_code=200)
def download_file(
    file_id: str, db: Session = Depends(get_db)
):
    """
    intro-->
            This endpoint returns a single file from the storage. To use this endpoint you need to make a get request to the /files/{bucket_name}/{file_name} endpoint

            paramDesc-->On get request the url takes two query parameters:
                
                    param-->file_id: This is the id of the file of interest

            returnDesc--> FileResponse

        Example:

            - Example 1 (Successful Request and Response):

                Request:
                {
                    "file_id": "<file_id>"
                }
                Response (200 OK):

                FileResponse


    """
    existing_file = db.query(Files).filter(Files.id == file_id).first()
    if existing_file:
        file_path = os.path.join(
            os.path.realpath(FILE_FOLDER),
            existing_file.bucket_name,
            existing_file.filename,
        )

        common_path = os.path.commonpath(
            (os.path.realpath(FILE_FOLDER), file_path)
        )
        if os.path.realpath(FILE_FOLDER) != common_path:
            raise HTTPException(
                status_code=403, detail="File reading from unallowed path"
            )
        

        return FileResponse(file_path, filename=existing_file.filename, media_type="video/webm")
    
@app.get("/files/{file_id}/thumbnail", status_code=200)
def get_thumbnail(
    file_id: str, db: Session = Depends(get_db)
):
    """
    intro-->
            This endpoint returns a single file from the storage. To use this endpoint you need to make a get request to the /files/{file_oid}/thumbnail endpoint

            paramDesc-->On get request the url takes two query parameters:
                
                    param-->file_id: This is the id of the file of interest

            returnDesc--> FileResponse

        Example:

            - Example 1 (Successful Request and Response):

                Request:
                {
                    "file_id": "<file_id>"
                }
                Response (200 OK):

                FileResponse

    """
    existing_file = db.query(Files).filter(Files.id == file_id).first()
    if existing_file:
        file_path = os.path.join(
            os.path.realpath(THUMBNAIL_FOLDER),
            existing_file.bucket_name,
            existing_file.thumbnail_name,
        )

        common_path = os.path.commonpath(
            (os.path.realpath(THUMBNAIL_FOLDER), file_path)
        )
        if os.path.realpath(THUMBNAIL_FOLDER) != common_path:
            raise HTTPException(
                status_code=403, detail="File reading from unallowed path"
            )

        return FileResponse(file_path, filename=existing_file.filename, media_type="image/jpeg")
    
@app.get("/files/{file_id}/playback", status_code=200)
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
                    "bucket_name": "<bucket_name>",
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
        file_path = os.path.join(
            os.path.realpath(FILE_FOLDER),
            existing_file.bucket_name,
            existing_file.filename,
        )

        
        return StreamingResponse(video_streamer(file_path), status_code=200, media_type="video/webm")


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
            os.path.realpath(FILE_FOLDER),
            existing_file.bucket_name,
            existing_file.filename,
        )

        common_path = os.path.commonpath(
            (os.path.realpath(FILE_FOLDER), local_file_path)
        )
        if os.path.realpath(FILE_FOLDER) != common_path:
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
    

    progress = db.query(Files).filter(Files.id == file_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "message": "progress retrieved successfully",
        "data": progress if progress else {}
    }