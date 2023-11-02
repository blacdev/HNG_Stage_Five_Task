from app.models import Files
from app.settings import settings
import os
from sqlalchemy.orm import Session
from db import SessionLocal
from moviepy.editor import *
import glob
import subprocess
from fastapi import Request
from app.services import get_url_full_path

FILE_FOLDER, BLOB_FOLDER, THUMBNAIL_FOLDER, COMPRESSION_FOLDER = settings.create_base_folders()

#  fucntion that finds all blobs that belong to a file
def find_blobs(file_id: str, db: Session):
    file = db.query(Files).filter(Files.id == file_id).first()
    if not file:
        return None
    return file


def   merge_blob(bucket_name:str, file_name:str, file_format:str = ".webm"):

    try:

        # sort file name in order
        blob_files = sorted(
            glob.glob(os.path.join(BLOB_FOLDER, bucket_name, f"*.{file_format}")),
            key=lambda x: int(x.split("_")[-1].split(".")[0]),
        )
    except Exception as err:
        raise Exception("error sorting blobs\nError: ", reason=err)

    new_file_name = f"{file_name}.{file_format}"

    # merge all files using moviepy
    clips = [VideoFileClip(file) for file in blob_files]
    try:
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(os.path.join(BLOB_FOLDER, bucket_name, new_file_name), codec="libx264")
        final_clip.close()
    except Exception as err:
        raise Exception("error merging blobs\nError: ", err)
    
    # move to compression folder
    os.rename(
        os.path.join(BLOB_FOLDER, bucket_name, new_file_name),
        os.path.join(COMPRESSION_FOLDER, bucket_name, new_file_name),
    )
    
    compressed_file_path = os.path.join(COMPRESSION_FOLDER, bucket_name, new_file_name)
    file_size = os.path.getsize(compressed_file_path)

    return compressed_file_path, file_size



def compress_video(input_path: str, output_path: str) -> None:
    """
    Compresses a video using ffmpeg.

    Parameters:
    - input_path: The path to the input video.
    - output_path: The path to the output video.

    Returns:
    - output_path: The path to the output video.

    Errors:
    - Exception: If an error occurs during video compression.

    """
    # ffmpeg -i input.webm -c:v libvpx -crf 30 -b:v 1M -c:a libvorbis output.mp4
    command = list()
    if input_path.endswith(".mp4"):
        command = [
            "ffmpeg",
            "-i",
            input_path,
            "-c:v",
            "libx264",
            "-crf",
            "30",
            "-b:v",
            "2M",
            "-c:a",
            "aac",
            output_path,
        ]

    else:
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

    try:
        subprocess.run(command, check=True)
        return output_path
    
    except subprocess.CalledProcessError as err:
        raise Exception("error compressing video\nError: ", err)
    


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
        "-ab",
        "32k",
        "-vframes",
        "1",
        thumbnail_path,
    ]
    try:
        subprocess.run(command, check=True)
        return thumbnail_path
    except subprocess.CalledProcessError as err:
        raise Exception("error extracting thumbnail\nError: ", err)


def is_valid_video(file_location: str) -> bool:
    """
    Check if a video file is valid by inspecting its metadata.
    Args:
        file_location (str): The location of the video file.
    Returns:
        bool: True if the video is valid, False otherwise.
    """
    metadata_command = ["ffmpeg", "-i", file_location]
    try:
        result = subprocess.run(
            metadata_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as err:
        return False



def process_video(file: Files, db: Session, request: Request):
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
        compressed_file_path, file_size = merge_blob(file.bucket_name, file.filename, file.file_format) 
        file.filesize = file_size

    except Exception as err:
        print(err)
        # Update the File's status to failed
        file.status = "failed"
        db.commit()
        db.refresh(file)
        return None
    
    file_name = f"{file.filename}.{file.file_format}"
    try:
        # Compress the video
        compressed_location = compress_video(compressed_file_path, os.path.join(FILE_FOLDER, file.bucket_name, file_name ))

    except Exception as err:
        print(err)

        # Update the File's status to failed
        file.status = "failed"
        db.commit()
        db.refresh(file)
        return None    
    # Extract a thumbnail
    thumbnail_location = extract_thumbnail(
        compressed_location, os.path.join(THUMBNAIL_FOLDER, file.bucket_name, file.thumbnail_name)
    )

    print("thumbnail_location", thumbnail_location)
    # Update the File's status to completed
    file = db.query(Files).filter(Files.id == file.id).first()
    file.status = "completed"
    file.compressed_filesize = os.path.getsize(os.path.join(COMPRESSION_FOLDER, file.bucket_name, file_name))
    file.download_url = get_url_full_path(request=request, file_type="video")
    file.thumbnail_url = get_url_full_path(request=request, file_type="thumbnail")
    file.play_back_url = get_url_full_path(request=request, file_type="playback")
    
    db.commit()
    db.refresh(file)

    # except Exception as err:
    #     print(err)
    #     # Update the File's status to failed
    #     file.status = "failed"
    # finally:
    #     db.commit()
    #     db.refresh(file)
    #     # end session
    #     db.close()
    #     # stop the process
    #     return None



def video_processing_start(file_id:str, request: Request):
    print("video_processing_start")
    with SessionLocal() as db:
        
        file = find_blobs(file_id, db)
        if not file:
            return None
        process_video(file, db, request)

    return "success"


