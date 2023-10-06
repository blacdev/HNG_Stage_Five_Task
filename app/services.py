from fastapi import Request
import os
from pprint import pprint
from typing import Union
from app.settings import settings

def getUrlFullPath(request: Request, file_id: str, type:Union[str, None] = None):
    hostname = request.headers.get("host")
    path = request.url.path
    
    request = f"{request.url.scheme}://"
    if request == "http://":
        if type == "video":
            return f"{hostname}{path}/{file_id}/download"


        elif type == "thumbnail":
           return f"{hostname}{path}/{file_id}/thumbnail"

        elif type == "playback":
            return f"{hostname}{path}/{file_id}/playback"

    elif request == "https://":
        if type == "video":
            return f"{hostname}{path}/{file_id}/download"

        elif type == "thumbnail":
            return f"{hostname}{path}/{file_id}/thumbnail"

        elif type == "playback":
            return f"{hostname}{path}/{file_id}/playback"




def append_to_file(file_path: str, file_name: str, bytes: bytes):
    with open(os.path.join(file_path, file_name), "ab") as f:
        f.write(bytes)



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

async def video_streamer(file_path: str):
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(1000000)
            if not chunk:
                break
            yield chunk