from app.models import Files, Chunk_tracker, Transcribe, Progress
from app.settings import settings
import os
from sqlalchemy.orm import Session
from db import SessionLocal
from pprint import pprint
from moviepy.editor import *


#  fucntion that finds all chunks that belong to a file
def find_chunks(file_id: str, bucket_name:str, file_name:str, is_chunk_complete:bool,db: Session):
    if is_chunk_complete:
        chunk_instances = db.query(Chunk_tracker).filter((Chunk_tracker.file_id == file_id) & (Chunk_tracker.is_completed == is_chunk_complete)).all()
    else:
        chunk_instances = db.query(Chunk_tracker).filter(Chunk_tracker.file_id == file_id, Chunk_tracker.is_completed == False).all()[:50]
        # print([chunk_instances.chunk_number for chunk_instances in chunk_instances])

    return chunk_instances, bucket_name, file_name

    

#  function that takes in a ".chunk" file and append it to the file it belongs to in files folder with a bucketname and filename
def append_chunk_to_file(chunk_instance_list:list, file_name:str, bucket_name:str, db: Session):
    file_path = os.path.join(settings.FILES_BASE_FOLDER, bucket_name, file_name)

    for chunk_instance in chunk_instance_list:
        print(chunk_instance.chunk_number, chunk_instance.file_id)
        Progress_instance = db.query(Progress).filter(Progress.file_id == chunk_instance.file_id).first()
        pprint(Progress_instance)
        chunk_path = os.path.join(settings.CHUNK_BASE_FOLDER, bucket_name, chunk_instance.chunk_name)
       
        # change file extension from .chunk to .webm
        if chunk_path.endswith(".chunk"):
            chunk_path = chunk_path.replace(".chunk", ".webm")

        try:
            # merge chunk vidoe with file video
            video = VideoFileClip(file_path)
            chunk_video = VideoFileClip(chunk_path)
            final_video = concatenate_videoclips([video, chunk_video])
            final_video.write_videofile(file_path)
  
            # update chunk tracker and progress
            if chunk_instance.is_last_chunk:
                chunk_instance.is_completed = True
                Progress_instance.progress  = chunk_instance.chunk_number
                Progress_instance.is_completed = True
                db.commit()
            else:
                chunk_instance.is_completed = True
                Progress_instance.progress = chunk_instance.chunk_number
                db.commit()
            os.remove(chunk_path)
        except Exception as e:
            print(e)
            print("error appending chunk to file")
            return False




async def video_processing_start(file_id:str, bucket_name:str, file_name:str,):

    with SessionLocal() as db:
        
        chunk_instances, bucket_name, file_name = find_chunks(file_id, bucket_name, file_name, False, db)
        append_chunk_to_file(chunk_instances, file_name, bucket_name, db)
    return bucket_name, file_name


