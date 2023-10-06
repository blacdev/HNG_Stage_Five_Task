from app.models import Files
from app.settings import settings
import os
from sqlalchemy.orm import Session
from db import SessionLocal
from moviepy.editor import *
import glob
import subprocess
from app.services import getUrlFullPath

FILE_FOLDER, BLOB_FOLDER, THUMBNAIL_FOLDER, COMPRESSION_FOLDER = settings.create_base_folders()

#  fucntion that finds all blobs that belong to a file
def find_blobs(file_id: str, db: Session):
    file = db.query(Files).filter(Files.id == file_id).first()
    if not file:
        return None
    return file

    
def video_processing_start(file_id:str):
    print("video_processing_start")
    with SessionLocal() as db:
        
        file = find_blobs(file_id, db)
        if not file:
            return None
        process_video(file, db)

    return "success"


def process_video(file: Files, db: Session):
    """
    Process a video by compressing it and extracting a thumbnail.

    Args:
        video_id (int): The ID of the video.
        file_location (str): The location of the video file.
        filename (str): The name of the video file.

    Raises:
        HTTPException: If an error occurs during video compression or thumbnail extraction.

    Returns:
        None
    """
    

    try:
        # merge all blobs and move to compression folder
        compressed_file_path, file_size = merge_blob(file.bucket_name, file.filename) 
        print(compressed_file_path)
        if is_valid_video(compressed_file_path) == False:
            print("invalid video at {}".format(compressed_file_path))

        file.filesize = file_size
        db.commit()


        # Compress the video
        compressed_location = compress_video(compressed_file_path, os.path.join(FILE_FOLDER, file.bucket_name, file.filename))
        if is_valid_video(compressed_location) == False:
            print("invalid video at {}".format(compressed_location))

        # Extract a thumbnail
        thumbnail_location = extract_thumbnail(
            compressed_location, os.path.join(THUMBNAIL_FOLDER, file.bucket_name, file.thumbnail_name)
        )
        if is_valid_video(thumbnail_location) == False:
            print("invalid thumbnail at {}".format(thumbnail_location))

        # Update the File's status to completed
        file.status = "completed"
        file.compressed_filesize = os.path.getsize(os.path.join(COMPRESSION_FOLDER, file.bucket_name, file.filename))
        file.download_url = getUrlFullPath(file.bucket_name, file.filename, "video")
        db.commit()
        db.refresh(file)

    except Exception as err:
        print(err)
        # Update the File's status to failed
        file.status = "failed"
    finally:
        db.commit()
        db.refresh(file)
        # end session
        db.close()
        # stop the process
        return None




def compress_video(input_path: str, output_path: str) -> None:
    """
    Compresses a video using ffmpeg.

    Parameters:
    - input_path: The path to the input video.
    - output_path: The path to the output video.

    Returns:
    - None

    """
    # ffmpeg -i input.webm -c:v libvpx -crf 30 -b:v 1M -c:a libvorbis output.webm


    command = [
        "ffmpeg",
        "-i",
        input_path,
        "-c:v",
        "libvpx",
        "-crf",
        "30",
        "-b:v",
        "1M",
        "-c:a",
        "libvorbis",
        output_path,
    ]
    subprocess.run(command, check=True)

    video_file_path = output_path

    return video_file_path


def extract_thumbnail(video_path: str, thumbnail_path: str) -> None:
    """
    Extracts a thumbnail from a video using ffmpeg.

    Parameters:
    - video_path: The path to the input video.
    - thumbnail_path: The path to the output thumbnail.

    Returns:
    - None

    """
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-ss",
        "00:00:00.000",
        "-vframes",
        "1",
        thumbnail_path,
    ]
    subprocess.run(command, check=True)


def is_valid_video(file_location: str) -> bool:
    """
    Check if a video file is valid by inspecting its metadata.
    Args:
        file_location (str): The location of the video file.
    Returns:
        bool: True if the video is valid, False otherwise.
    """
    metadata_command = ["ffmpeg", "-i", file_location]
    result = subprocess.run(
        metadata_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    msg = "Invalid data found when processing input"
    return msg not in result.stderr



def merge_blob(bucket_name:str, file_name:str):

    # sort file name in order
    blob_files = sorted(
        glob.glob(os.path.join(BLOB_FOLDER, bucket_name, "*.webm")),
        key=lambda x: int(x.split("_")[-1].split(".")[0]),
    )
    # # merge all files
    # with open(os.path.join(BLOB_FOLDER, bucket_name, file_name), "wb") as outfile:
    #     for file in blob_files:
    #         with open(file, "rb") as readfile:
    #             outfile.write(readfile.read())

    # merge all files using moviepy
    clips = []
    for file in blob_files:
        clips.append(VideoFileClip(file))
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(os.path.join(BLOB_FOLDER, bucket_name, file_name))
    final_clip.close()

    import time
    time.sleep(15)
    # move to compression folder
    os.rename(
        os.path.join(BLOB_FOLDER, bucket_name, file_name),
        os.path.join(COMPRESSION_FOLDER, bucket_name, file_name),
    )
    
    
    compressed_file_path = os.path.join(COMPRESSION_FOLDER, bucket_name, file_name)
    print(compressed_file_path)
    file_size = os.path.getsize(compressed_file_path)
    

    return compressed_file_path, file_size
