from fastapi import FastAPI, Depends, HTTPException, UploadFile,File, Request
import uvicorn
import os
from uuid import uuid4
from datetime import datetime
from fastapi.responses import FileResponse
from models import Files, find_file
from db import get_db, create_database
from sqlalchemy import and_
from sqlalchemy.orm import Session
from settings import settings
from schemas import FileSchema
from fastapi.middleware.cors import CORSMiddleware

def getUrlFullPath(request: Request, filename: str, bucket_name: str = None):
    hostname = request.headers.get("host")
    request = f"{request.url.scheme}://"
    if hostname == "127.0.0.1:8000":
        hostname = request + hostname
    else:
        hostname = f"https://{hostname}"  

    return f"{hostname}/files/{bucket_name}/{filename}"




app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_database()




@app.post("/upload-file/{bucket_name}/", response_model=FileSchema)
async def upload_file(
    request: Request,
    bucket_name: str,
    file: UploadFile = File(...),
    file_rename: bool = False,
    db: Session = Depends(get_db),
):
    """intro-->This endpoint allows you to upload a file to a bucket/storage. To use this endpoint you need to make a post request to the /upload-file/{bucket_name}/ endpoint
        paramDesc-->On post request the url takes the query parameter bucket_name
            param-->bucket_name: This is the name of the bucket you want to save the file to, You can request a list of files in a single folder if you nee to iterate.
            param-->file_rename: This is a boolean value that if set to true renames the hex values
            param-->width: width of thumbnail to be created from image
            param-->height: height of thumbnail to be created from image
            param-->scale: How to scale image when generating thumbnail; options are width or height or ""
            param-->create_thumbnail: Whether to generate thumbnail or not
    returnDesc--> On successful request, it returns
    returnBody--> details of the file just created
    """

    # Make sure the base folder exists
    if settings.FILES_BASE_FOLDER == None or len(settings.FILES_BASE_FOLDER) < 2:
        raise HTTPException(status_code=404, detail="This title already exists")

    # Make sure the bucket name does not contain any paths
    if bucket_name.isalnum() == False:
        raise HTTPException(
            status_code=406, detail="Bucket name has to be alpha-numeric"
        )

    # Create the base folder
    base_folder = os.path.realpath(settings.FILES_BASE_FOLDER)
    try:
        os.makedirs(base_folder)
    except:
        pass

    # Make sure bucket name exists
    try:
        os.makedirs(os.path.join(base_folder, bucket_name))
    except:
        pass
    if file_rename == True:
        file_type = file.filename.split(".")[-1]
        file.filename = str(uuid4().hex + "." + file_type)

    full_write_path = os.path.realpath(
        os.path.join(base_folder, bucket_name, file.filename)
    )

    # Make sure there has been no exit from our core folder
    common_path = os.path.commonpath((full_write_path, base_folder))
    if base_folder != common_path:
        raise HTTPException(
            status_code=403, detail="File writing to unallowed path"
        )

    contents = await file.read()

    # Try to write file. Throw exception if anything bad happens
    try:
        with open(full_write_path, "wb") as f:
            f.write(contents)
    except OSError:
        raise HTTPException(status_code=423, detail="Error writing to the file")

    # Retrieve the file size from what we wrote on disk, so we are sure it matches
    filesize = os.path.getsize(full_write_path)

    # Check if the file exists
    existing_file = find_file(bucket_name, file.filename, db)
    if existing_file:
        existing_file.filesize = filesize
        existing_file.last_updated = datetime.utcnow()
        existing_file.url = getUrlFullPath(request, file.filename, bucket_name)
        db.commit()
        db.refresh(existing_file)

        return existing_file 
    else:
        # Create a db entry for this file.
        file = Files(
            id=uuid4().hex,
            filename=file.filename,
            bucketname=bucket_name,
            filesize=filesize,
            url=getUrlFullPath(request, file.filename, bucket_name),
        )
        db.add(file)
        db.commit()
        db.refresh(file)

        return FileSchema.from_orm(file)
    

@app.get("/files/{bucket_name}/{file_name}" )
def get_file(
    bucket_name: str, file_name: str, db: Session = Depends(get_db)
):

    """Download a single file from the storage

    Args:
        bucket_name (str): the bucket to list all the files.
        file_name (str): the file that you want to retrieve

    Returns:
        A url of the file
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



@app.get(
    "/files/{bucket_name}/",
    # response_model=List[FileSchema]
)
def get_all_files(request:Request, bucket_name: str, db: Session = Depends(get_db)):
    """intro-->This endpoint returns all files that are in a single bucket. To use this endpoint you need to make a get request to the /files/{bucket_name}/ endpoint
            paramDesc-->On get request the url takes a query parameter bucket_name
                param-->bucket_name: This is the name of the bucket containing files of interest
    returnDesc--> On successful request, it returns
        returnBody--> a list of all files in the bucket
    """
    files = db.query(Files).filter(Files.bucketname == bucket_name).all()
    response = []
    for file in files:
        local_file_path = os.path.join(
            os.path.realpath(settings.FILES_BASE_FOLDER), file.bucketname, file.filename
        )
        common_path = os.path.commonpath(
            (os.path.realpath(settings.FILES_BASE_FOLDER), local_file_path)
        )
        if os.path.realpath(settings.FILES_BASE_FOLDER) != common_path:
            raise HTTPException(
                status_code=403, detail="File reading from unallowed path"
            )

        response.append(FileSchema.from_orm(file))
    return response




# delete file
@app.delete("/files/{bucket_name}/{file_name}")
def delete_file(
    bucket_name: str, file_name: str, db: Session = Depends(get_db)
):
    """Delete a single file from the storage

    Args:
        bucket_name (str): the bucket to list all the files.
        file_name (str): the file that you want to delete

    Returns:
        A stream of the file
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




if __name__ == "__main__":
    uvicorn.run(app= 'main:app', port=8000, reload=True)