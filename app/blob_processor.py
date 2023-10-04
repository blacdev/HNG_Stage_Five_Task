from app.models import Blob_tracker, Progress, Files
from app.settings import settings
import os
from sqlalchemy.orm import Session
from db import SessionLocal
from moviepy.editor import *
from app.services import create_empty_file


#  fucntion that finds all blobs that belong to a file
def find_blobs(file_id: str, db: Session):
    file = db.query(Files).filter(Files.id == file_id).first()
    if not file:
        quit("file not found")
    blob_instances = db.query(Blob_tracker).filter(Blob_tracker.file_id == file_id, Blob_tracker.is_completed == False).order_by(Blob_tracker.blob_sequnce).all()
    if not blob_instances:
        quit("no blob instances found")

    return blob_instances, file.bucketname, file.filename

    

#  function that takes in a ".blob" file and append it to the file it belongs to in files folder with a bucketname and filename
def append_blob_to_file(blob_instance_list:list[Blob_tracker], file_name:str, bucket_name:str, db: Session):

    blob_count = len(blob_instance_list)
    update_progress(file_id=blob_instance_list[0].file_id, db=db, expected_progress_count=blob_count)

    for blob_instance in blob_instance_list:

        file_path = os.path.join(settings.FILES_BASE_FOLDER, bucket_name, file_name)
        if not os.path.exists(file_path):
            create_empty_file(file_name, bucket_name)
            

        # get file size
        file_size = os.path.getsize(file_path)

        blob_path = os.path.join(settings.BLOB_BASE_FOLDER, bucket_name, blob_instance.blob_name)
       

        if file_size == 0:
            # grab blob and append to file using moviepy
            blob = VideoFileClip(blob_path)
            blob.write_videofile(file_path)

            # update blob 
            update_blob_tracker(file_id=blob_instance.file_id, blob_sequnce=blob_instance.blob_sequnce, db=db, is_completed=True)
            update_progress(file_id=blob_instance.file_id, db=db, progress_position=blob_instance.blob_sequnce)

            # remove blob
            os.remove(blob_path)

        
        else:
            #  use moviepy to append file
            blob_video = VideoFileClip(blob_path)
            video = VideoFileClip(file_path)
            video = concatenate_videoclips([video, blob_video])
            video.write_videofile(file_path)


            # update progress
            update_progress(file_id=blob_instance.file_id, db=db, progress_position=blob_instance.blob_sequnce)


            # remove blob
            os.remove(blob_path)


            
            
def update_progress(file_id:str, db:Session, progress_position:int=None, expected_progress_count:int = None, is_completed:bool = False):
    progress_instance = db.query(Progress).filter(Progress.file_id == file_id).first()

    if progress_position != None:
        progress_position = progress_position
    
    else:
        progress_position = progress_instance.progress_position

    if expected_progress_count != None:
        expected_progress_count = expected_progress_count
    else:
        expected_progress_count = progress_instance.expected_progress_count
    
    if is_completed != False:
        is_completed = is_completed
    else:
        is_completed = progress_instance.is_completed

    progress_instance.progress_position = progress_position
    progress_instance.expected_progress_count = expected_progress_count
    progress_instance.is_completed = is_completed

    db.commit()
    db.refresh(progress_instance)

    
#  function to update blob tracker
def update_blob_tracker(file_id:str, blob_sequnce:int, db:Session, is_completed:bool = False):
    blob_instance = db.query(Blob_tracker).filter((Blob_tracker.file_id == file_id) & (Blob_tracker.blob_sequnce == blob_sequnce)).first()
    blob_instance.is_completed = is_completed
    db.commit()
    db.refresh(blob_instance)



def video_processing_start(file_id:str):
    print("video_processing_start")
    with SessionLocal() as db:
        
        blob_instances, bucket_name, file_name = find_blobs(file_id, db)
        append_blob_to_file(blob_instances, file_name, bucket_name, db)

    return "success"




